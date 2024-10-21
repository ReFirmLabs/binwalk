use crate::common::is_offset_safe;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::cpio;

/// Human readable description
pub const DESCRIPTION: &str = "CPIO ASCII archive";

/// Magic bytes for CPIO archives with and without CRC's
pub fn cpio_magic() -> Vec<Vec<u8>> {
    vec![b"070701".to_vec(), b"070702".to_vec()]
}

/// Parse and validate CPIO archives
pub fn cpio_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // The last CPIO entry will have this file name
    const EOF_MARKER: &str = "TRAILER!!!";

    let mut header_count: usize = 0;
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        offset,
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let mut next_header_offset = offset;
    let mut previous_header_offset = None;
    let available_data = file_data.len();

    // Loop over all the available data, or until CPIO EOF, or until error
    while is_offset_safe(available_data, next_header_offset, previous_header_offset) {
        // Get the CPIO entry's raw data
        match file_data.get(next_header_offset..) {
            None => {
                break;
            }
            Some(cpio_entry_data) => {
                // Parse this CPIO entry's header
                match cpio::parse_cpio_entry_header(cpio_entry_data) {
                    Err(_) => {
                        break;
                    }
                    Ok(cpio_header) => {
                        // Sanity check the magic bytes
                        if !cpio_magic().contains(&cpio_header.magic) {
                            break;
                        }

                        // Keep a tally of how many CPIO headers have been processed
                        header_count += 1;

                        // Update the total size of the CPIO file to include this header and its data
                        result.size += cpio_header.header_size + cpio_header.data_size;

                        // If EOF marker has been found, we're done
                        if cpio_header.file_name == EOF_MARKER {
                            // If one or fewer CPIO headers were found, consider it a false positive;
                            // a CPIO archive should have at least one file/directory entry, and one EOF entry.
                            if header_count > 1 {
                                // Return the result; reported file count does not include the EOF entry
                                result.description = format!(
                                    "{}, file count: {}",
                                    result.description,
                                    header_count - 1
                                );
                                return Ok(result);
                            }

                            break;
                        }

                        // Update the previous and next header offset values for the next loop iteration
                        previous_header_offset = Some(next_header_offset);
                        next_header_offset = offset + result.size;
                    }
                }
            }
        }
    }

    // No EOF marker was found, or an error occurred in processing the CPIO headers
    Err(SignatureError)
}
