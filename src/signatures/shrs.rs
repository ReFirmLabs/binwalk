use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use crate::structures::shrs::parse_shrs_header;

/// Human readable description
pub const DESCRIPTION: &str = "SHRS encrypted firmware";

/// SHRS firmware images always start with these bytes
pub fn shrs_magic() -> Vec<Vec<u8>> {
    vec![b"SHRS".to_vec()]
}

/// Validates the SHRS header
pub fn shrs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(shrs_header) = parse_shrs_header(&file_data[offset..]) {
        result.size = shrs_header.header_size + shrs_header.data_size;
        result.description = format!(
            "{}, header size: {} bytes, encrypted data size: {} bytes, IV: {}",
            result.description,
            shrs_header.header_size,
            shrs_header.data_size,
            hex::encode(shrs_header.iv),
        );

        if offset == 0 {
            result.confidence = CONFIDENCE_MEDIUM;
        }

        return Ok(result);
    }

    Err(SignatureError)
}
