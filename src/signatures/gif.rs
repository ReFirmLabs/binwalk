use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};

/// Human readable description
pub const DESCRIPTION: &str = "GIF image";

/// GIF images always start with these bytes
pub fn gif_magic() -> Vec<Vec<u8>> {
    return vec![
        b"GIF87a".to_vec(),
        b"GIF89a".to_vec(),
        ];
}

/// Validates the GIF header
pub fn gif_parser(_file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // TODO: Further parsing/validation of gif data
    return Ok(result);
}
