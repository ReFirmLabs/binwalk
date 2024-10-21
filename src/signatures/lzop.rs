use crate::common::is_offset_safe;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::lzop::{
    parse_lzop_block_header, parse_lzop_eof_marker, parse_lzop_file_header,
};

/// Human readable description
pub const DESCRIPTION: &str = "LZO compressed data";

/// LZOP magic bytes
pub fn lzop_magic() -> Vec<Vec<u8>> {
    vec![b"\x89LZO\x00\x0D\x0A\x1A\x0A".to_vec()]
}

/// Validate an LZOP signature
pub fn lzop_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success retrun value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the LZOP file header
    if let Ok(lzop_header) = parse_lzop_file_header(&file_data[offset..]) {
        if let Some(lzop_data) = file_data.get(offset + lzop_header.header_size..) {
            // Get the size of the compressed LZO data
            if let Ok(data_size) = get_lzo_data_size(lzop_data, lzop_header.block_checksum_present)
            {
                // Update the total size to include the LZO data
                result.size = lzop_header.header_size + data_size;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}

// Parse the LZO blocks to determine the size of the compressed data, including the terminating EOF marker
fn get_lzo_data_size(
    lzo_data: &[u8],
    compressed_checksum_present: bool,
) -> Result<usize, SignatureError> {
    // Technially LZOP could have one block, but this would seem uncommon
    const MIN_BLOCK_COUNT: usize = 2;

    let available_data = lzo_data.len();
    let mut last_offset = None;
    let mut data_size: usize = 0;
    let mut block_count: usize = 0;

    // Loop until we run out of data or an invalid block header is encountered
    while is_offset_safe(available_data, data_size, last_offset) {
        // Parse the next block header
        match parse_lzop_block_header(&lzo_data[data_size..], compressed_checksum_present) {
            Err(_) => {
                break;
            }

            Ok(block_header) => {
                // Update block count, offset, and size
                block_count += 1;
                last_offset = Some(data_size);
                data_size += block_header.header_size
                    + block_header.compressed_size
                    + block_header.checksum_size;
            }
        }
    }

    // As a sanity check, make sure we processed some number of data blocks
    if block_count >= MIN_BLOCK_COUNT {
        // Process the EOF marker that should come at the end of the data blocks
        if let Some(eof_marker_data) = lzo_data.get(data_size..) {
            if let Ok(eof_marker_size) = parse_lzop_eof_marker(eof_marker_data) {
                data_size += eof_marker_size;
                return Ok(data_size);
            }
        }
    }

    Err(SignatureError)
}
