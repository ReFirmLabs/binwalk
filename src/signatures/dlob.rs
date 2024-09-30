use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};
use crate::structures::dlob::parse_dlob_header;

/// Human readable description
pub const DESCRIPTION: &str = "DLOB firmware header";

/// DLOB firmware images always start with these bytes
pub fn dlob_magic() -> Vec<Vec<u8>> {
    return vec![b"\x5e\xa3\xa4\x17".to_vec()];
}

/// Validates the DLOB header
pub fn dlob_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(dlob_header) = parse_dlob_header(&file_data[offset..]) {
        result.size = dlob_header.size;
        result.description = format!("{}, header size: {} bytes", result.description, result.size);
        return Ok(result);
    }

    return Err(SignatureError);
}
