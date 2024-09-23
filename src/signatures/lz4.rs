use crate::signatures;
use crate::structures::lz4::{parse_lz4_block_header, parse_lz4_file_header};

pub const DESCRIPTION: &str = "LZ4 compressed data";

pub fn lz4_magic() -> Vec<Vec<u8>> {
    return vec![b"\x04\x22\x4D\x18".to_vec()];
}

pub fn lz4_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const CONTENT_CHECKSUM_LEN: usize = 4;

    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        confidence: signatures::common::CONFIDENCE_MEDIUM,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    // Sanity check the size of available data
    if let Ok(lz4_file_header) = parse_lz4_file_header(&file_data[offset..]) {
        // Sanity check the reported header size
        if lz4_file_header.header_size < available_data {
            // Determine the size of the actual LZ4 data by processing the data blocks that immediately follow the file header
            if let Ok(lz4_data_size) = get_lz4_data_size(
                &file_data[lz4_file_header.header_size..],
                lz4_file_header.block_checksum_present,
            ) {
                // Set the size of the header and the LZ4 data
                result.size = lz4_file_header.header_size + lz4_data_size;

                // If this flag is set, an additional 4-byte checksum will be present at the end of the LZ4 data
                if lz4_file_header.content_checksum_present == true {
                    result.size += CONTENT_CHECKSUM_LEN;
                }

                // Update description
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);

                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}

// Processes the LZ4 data blocks and returns the size of the raw LZ4 data
fn get_lz4_data_size(
    lz4_data: &[u8],
    checksum_present: bool,
) -> Result<usize, signatures::common::SignatureError> {
    let mut lz4_data_size: usize = 0;

    // Loop through data blocks while there is still data left to processes
    while lz4_data.len() > lz4_data_size {
        match parse_lz4_block_header(&lz4_data[lz4_data_size..], checksum_present) {
            Err(_) => {
                break;
            }

            Ok(block_header) => {
                lz4_data_size +=
                    block_header.header_size + block_header.data_size + block_header.checksum_size;

                if block_header.last_block == true {
                    return Ok(lz4_data_size);
                }
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
