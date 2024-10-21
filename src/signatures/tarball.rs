use crate::common::is_offset_safe;
use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
};

/// Some tarball constants
const TARBALL_BLOCK_SIZE: usize = 512;
const TARBALL_MAGIC_OFFSET: usize = 257;
const TARBALL_MAGIC_SIZE: usize = 5;
const TARBALL_SIZE_OFFSET: usize = 124;
const TARBALL_SIZE_LEN: usize = 11;
const TARBALL_UNIVERSAL_MAGIC: &[u8; 5] = b"ustar";
const TARBALL_MIN_EXPECTED_HEADERS: usize = 10;

/// Human readable description
pub const DESCRIPTION: &str = "POSIX tar archive";

/// Magic bytes for tarball and GNU tarball file types
pub fn tarball_magic() -> Vec<Vec<u8>> {
    vec![b"ustar\x00".to_vec(), b"ustar\x20\x20\x00".to_vec()]
}

/// Validate tarball signatures
pub fn tarball_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Stores the running total size of the tarball
    let mut tarball_total_size: usize = 0;

    // Keep a count of how many tar entry headers were validated
    let mut valid_header_count: usize = 0;

    // Calculate the actual start of the tarball (header magic does not start at the beginning of a tar entry)
    let tarball_start_offset = offset - TARBALL_MAGIC_OFFSET;

    // Tarball magic bytes do not start at the beginning of the tarball file
    let mut next_header_start = tarball_start_offset;
    let mut previous_header_start = None;
    let available_data = file_data.len();

    // Loop through available data, processing tarball entry headers
    while is_offset_safe(available_data, next_header_start, previous_header_start) {
        // Calculate the end of the next tarball entry data
        let next_header_end = next_header_start + TARBALL_BLOCK_SIZE;

        // Get the next header's data; this will fail if not enough data is present, protecting
        // other functions (header_checksum_is_valid, tarball_entry_size) from out-of-bounds access
        match file_data.get(next_header_start..next_header_end) {
            None => {
                break;
            }
            Some(tarball_header_block) => {
                // Bad checksum? Quit processing headers.
                if !header_checksum_is_valid(tarball_header_block) {
                    break;
                }

                // Increment the count of valid tarball headers found
                valid_header_count += 1;

                // Get the reported size of the next entry header
                match tarball_entry_size(tarball_header_block) {
                    Err(_) => {
                        break;
                    }
                    Ok(entry_size) => {
                        // Update total size count, and next/previous header offsets
                        tarball_total_size += entry_size;
                        previous_header_start = Some(next_header_start);
                        next_header_start += entry_size;
                    }
                }
            }
        }
    }

    // We expect that a tarball should be, at a minimum, one block in size
    if tarball_total_size >= TARBALL_BLOCK_SIZE {
        // Default confidence is medium
        let mut confidence = CONFIDENCE_MEDIUM;

        // If more than just a few tarball headers were found and processed successfully, we have pretty high confidence that this isn't a false positive
        if valid_header_count >= TARBALL_MIN_EXPECTED_HEADERS {
            confidence = CONFIDENCE_HIGH;
        }

        return Ok(SignatureResult {
            description: format!("{}, file count: {}", DESCRIPTION, valid_header_count),
            offset: tarball_start_offset,
            size: tarball_total_size,
            confidence,
            ..Default::default()
        });
    }

    Err(SignatureError)
}

/// Validate a tarball entry checksum
fn header_checksum_is_valid(header_block: &[u8]) -> bool {
    const TARBALL_CHECKSUM_START: usize = 148;
    const TARBALL_CHECKSUM_END: usize = 156;

    let checksum_value_string: &[u8] = &header_block[TARBALL_CHECKSUM_START..TARBALL_CHECKSUM_END];
    let reported_checksum = tarball_octal(checksum_value_string);
    let mut sum: usize = 0;

    for (i, header_byte) in header_block.iter().enumerate() {
        if (TARBALL_CHECKSUM_START..TARBALL_CHECKSUM_END).contains(&i) {
            sum += 0x20;
        } else {
            sum += *header_byte as usize;
        }
    }

    sum == reported_checksum
}

/// Returns the size of a tarball entry, including header and data
fn tarball_entry_size(tarball_entry_data: &[u8]) -> Result<usize, SignatureError> {
    // Get the tarball entry's magic bytes
    let entry_magic: &[u8] =
        &tarball_entry_data[TARBALL_MAGIC_OFFSET..TARBALL_MAGIC_OFFSET + TARBALL_MAGIC_SIZE];

    // Make sure the magic bytes are valid
    if entry_magic == TARBALL_UNIVERSAL_MAGIC {
        // Pull this tarball entry's data size, stored as ASCII octal, out of the header
        let entry_size_string: &[u8] =
            &tarball_entry_data[TARBALL_SIZE_OFFSET..TARBALL_SIZE_OFFSET + TARBALL_SIZE_LEN];

        // Convert the ASCII octal to a number
        let reported_entry_size: usize = tarball_octal(entry_size_string);

        // The actual size of this entry will be the data size, rounded up to the nearest block size, PLUS one block for the entry header
        let block_count: usize =
            1 + (reported_entry_size as f32 / TARBALL_BLOCK_SIZE as f32).ceil() as usize;

        // Total size is the total number of blocks times the block size
        return Ok(block_count * TARBALL_BLOCK_SIZE);
    }

    Err(SignatureError)
}

/// Convert octal string to a number
fn tarball_octal(octal_string: &[u8]) -> usize {
    let mut num: usize = 0;

    for octal_char in octal_string {
        // ASCII octal values should be ASCII
        if *octal_char < 0x30 || *octal_char > 0x39 {
            break;
        } else {
            num *= 8;
            num = num + (*octal_char as usize) - 0x30;
        }
    }

    num
}
