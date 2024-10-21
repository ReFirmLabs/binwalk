use crate::common::is_offset_safe;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::lzfse::parse_lzfse_block_header;

/// Human readable description
pub const DESCRIPTION: &str = "LZFSE compressed data";

/// LZFSE block magics
pub fn lzfse_magic() -> Vec<Vec<u8>> {
    vec![
        b"bvx-".to_vec(),
        b"bvx1".to_vec(),
        b"bvx2".to_vec(),
        b"bvxn".to_vec(),
    ]
}

/// Validate LZFSE signatures
pub fn lzfse_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        confidence: CONFIDENCE_HIGH,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let available_data = file_data.len();
    let mut next_block_offset = offset;
    let mut previous_block_offset = None;

    // Walk through all the LZFSE blocks until an end of stream block is found
    while is_offset_safe(available_data, next_block_offset, previous_block_offset) {
        // Update previous block offset value in preparation for the next loop
        previous_block_offset = Some(next_block_offset);

        // Parse the next block
        if let Ok(lzfse_block) = parse_lzfse_block_header(&file_data[next_block_offset..]) {
            next_block_offset += lzfse_block.header_size + lzfse_block.data_size;

            // Only return success if an end-of-stream block is found
            if lzfse_block.eof {
                result.size = next_block_offset - offset;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
