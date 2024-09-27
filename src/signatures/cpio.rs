use crate::common::is_offset_safe;
use crate::signatures;
use crate::structures::cpio;

pub const DESCRIPTION: &str = "CPIO ASCII archive";

pub fn cpio_magic() -> Vec<Vec<u8>> {
    return vec![b"070701".to_vec(), b"070702".to_vec()];
}

pub fn cpio_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const EOF_MARKER: &str = "TRAILER!!!";

    let mut header_count: usize = 0;
    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        offset: offset,
        size: 0,
        confidence: signatures::common::CONFIDENCE_HIGH,
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
                        if cpio_magic().contains(&cpio_header.magic) == false {
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
    return Err(signatures::common::SignatureError);
}
