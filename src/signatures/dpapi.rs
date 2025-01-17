use crate::signatures::common::{SignatureError, SignatureResult};

use super::common::CONFIDENCE_MEDIUM;

/// Human readable description
pub const DESCRIPTION: &str = "DPAPI blob data";

/// DPAPI blob data header will always start with these bytes
pub fn dpapi_magic() -> Vec<Vec<u8>> {
    vec![b"\x01\x00\x00\x00\xD0\x8c\x9d\xdf\x01\x15\xd1\x11\x8c\x7a\x00\xc0\x4f\xc2\x97\xeb".to_vec()]
}

/// Returns success with additional details
pub fn dpapi_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    Ok(result)
}