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

    // Loop while there is still the possibility of having a CPIO header
    while file_data.len() >= (offset + result.size + cpio::CPIO_HEADER_SIZE) {
        // Calculate the start and end offsets, enough to process a CPIO header with an EOF marker
        let header_data_start: usize = offset + result.size;

        // Parse this CPIO entry's header
        if let Ok(cpio_header) = cpio::parse_cpio_entry_header(&file_data[header_data_start..]) {
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
                // We should have processed more than just an EOF entry!
                if header_count > 1 {
                    result.description =
                        format!("{}, file count: {}", result.description, header_count - 1);
                    return Ok(result);
                } else {
                    break;
                }
            }
        } else {
            break;
        }
    }

    // No EOF marker was found, or an error occurred in processing the CPIO headers
    return Err(signatures::common::SignatureError);
}
