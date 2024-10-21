use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};
use crate::structures::seama::parse_seama_header;

/// Human readable description
pub const DESCRIPTION: &str = "SEAMA firmware header";

/// SEAMA magic bytes, big and little endian
pub fn seama_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x5E\xA3\xA4\x17\x00\x00".to_vec(),
        b"\x17\xA4\xA3\x5E\x00\x00".to_vec(),
    ]
}

/// Validate SEAMA signatures
pub fn seama_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Parse the header
    if let Ok(seama_header) = parse_seama_header(&file_data[offset..]) {
        let total_size: usize = seama_header.header_size + seama_header.data_size;

        // Sanity check the reported size
        if file_data.len() >= (offset + total_size) {
            result.size = seama_header.header_size;
            result.description = format!(
                "{}, header size: {} bytes, data size: {} bytes",
                result.description, seama_header.header_size, seama_header.data_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
