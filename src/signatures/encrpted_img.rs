use crate::signatures::common::{
    CONFIDENCE_LOW, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};

/// Human readable description
pub const DESCRIPTION: &str = "D-Link Encrpted Image";

/// encrpted_img firmware images always start with these bytes
pub fn encrpted_img_magic() -> Vec<Vec<u8>> {
    vec![b"encrpted_img".to_vec()]
}

/// Validates the encrpted_img header
pub fn encrpted_img_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Nothing to really validate here
    if offset != 0 {
        result.confidence = CONFIDENCE_LOW;
    }

    Ok(result)
}
