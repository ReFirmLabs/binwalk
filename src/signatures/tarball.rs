use crate::signatures;

const TARBALL_BLOCK_SIZE: usize = 512;
const TARBALL_MAGIC_OFFSET: usize = 257;
const TARBALL_MAGIC_SIZE: usize = 5;
const TARBALL_SIZE_OFFSET: usize = 124;
const TARBALL_SIZE_LEN: usize = 11;
const TARBALL_UNIVERSAL_MAGIC: &[u8; 5] = b"ustar";
const TARBALL_MIN_EXPECTED_HEADERS: usize = 10;

pub const DESCRIPTION: &str = "POSIX tar archive";

pub fn tarball_magic() -> Vec<Vec<u8>> {
    return vec![b"ustar\x00".to_vec(), b"ustar\x20\x20\x00".to_vec()];
}

pub fn tarball_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // Stores the running total size of the tarball
    let mut tarball_total_size: usize = 0;

    // Keep a count of how many tar entry headers were validated
    let mut valid_header_count: usize = 0;

    // Calculate the actual start of the tarball (header magic does not start at the beginning of a tar entry)
    let tarball_start_offset = offset - TARBALL_MAGIC_OFFSET;

    // Loop through available data, processing tarball entry headers
    while file_data.len() > (tarball_start_offset + tarball_total_size + TARBALL_BLOCK_SIZE) {
        // Calculate the offset(s) of the next expected tarball entry header
        let next_header_start = tarball_start_offset + tarball_total_size;
        let next_header_end = next_header_start + TARBALL_BLOCK_SIZE;

        // usize overflow
        if next_header_end < next_header_start {
            break;
        }

        // Get the next header's block
        let tarball_header_block: &[u8] = &file_data[next_header_start..next_header_end];

        // Bad checksum? Quit processing headers.
        if header_checksum_is_valid(tarball_header_block) == false {
            break;
        }

        // Get the reported size of the next entry header
        match tarball_entry_size(tarball_header_block) {
            Err(_e) => break,
            Ok(entry_size) => {
                // Sanity check: tarball should not extend beyond EOF
                if (tarball_start_offset + tarball_total_size + entry_size) <= file_data.len() {
                    // Append this entry's size to the running total
                    tarball_total_size = tarball_total_size + entry_size;
                    valid_header_count += 1;
                } else {
                    break;
                }
            }
        }
    }

    // We expect that a tarball should be, at a minimum, one block in size
    if tarball_total_size >= TARBALL_BLOCK_SIZE {
        // Default confidence is medium
        let mut confidence = signatures::common::CONFIDENCE_MEDIUM;

        // If more than just a few tarball headers were found and processed successfully, we have pretty high confidence that this isn't a false positive
        if valid_header_count >= TARBALL_MIN_EXPECTED_HEADERS {
            confidence = signatures::common::CONFIDENCE_HIGH;
        }

        return Ok(signatures::common::SignatureResult {
            description: format!("{}, file count: {}", DESCRIPTION, valid_header_count),
            offset: tarball_start_offset,
            size: tarball_total_size,
            confidence: confidence,
            ..Default::default()
        });
    }

    return Err(signatures::common::SignatureError);
}

fn header_checksum_is_valid(header_block: &[u8]) -> bool {
    const TARBALL_CHECKSUM_START: usize = 148;
    const TARBALL_CHECKSUM_END: usize = 156;

    let checksum_value_string: &[u8] = &header_block[TARBALL_CHECKSUM_START..TARBALL_CHECKSUM_END];
    let reported_checksum = tarball_octal(checksum_value_string);
    let mut sum: usize = 0;

    for i in 0..header_block.len() {
        if i >= TARBALL_CHECKSUM_START && i < TARBALL_CHECKSUM_END {
            sum = sum + 0x20;
        } else {
            sum = sum + (header_block[i] as usize);
        }
    }

    return sum == reported_checksum;
}

fn tarball_entry_size(
    tarball_entry_data: &[u8],
) -> Result<usize, signatures::common::SignatureError> {
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

    return Err(signatures::common::SignatureError);
}

// Convert octal string to a number
fn tarball_octal(octal_string: &[u8]) -> usize {
    let mut num: usize = 0;

    for i in 0..octal_string.len() {
        // ASCII octal values should be ASCII
        if octal_string[i] < 0x30 || octal_string[i] > 0x39 {
            break;
        } else {
            num = num * 8;
            num = num + (octal_string[i] as usize) - 0x30;
        }
    }

    return num;
}
