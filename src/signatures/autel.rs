use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::autel::parse_autel_header;

/// Human readable description
pub const DESCRIPTION: &str = "Autel obfuscated firmware";

/// Autel magic bytes
pub fn autel_magic() -> Vec<Vec<u8>> {
    vec![b"ECC0101\x00".to_vec()]
}

/// Validates the Autel header
pub fn autel_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(autel_header) = parse_autel_header(&file_data[offset..]) {
        result.size = autel_header.header_size + autel_header.data_size;
        result.description = format!(
            "{}, header size: {} bytes, data size: {}, total size: {}",
            result.description, autel_header.header_size, autel_header.data_size, result.size
        );
        return Ok(result);
    }

    Err(SignatureError)
}
