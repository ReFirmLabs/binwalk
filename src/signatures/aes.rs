use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};

/// Human readable description
pub const DESCRIPTION: &str = "AES S-Box";

/// AES S-box magic bytes
pub fn aes_sbox_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x63\x7C\x77\x7B\xF2\x6B\x6F\xC5".to_vec(),
        b"\x52\x09\x6A\xD5\x30\x36\xA5\x38".to_vec(),
    ]
}

/// Validates the AES S-Box
pub fn aes_sbox_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}
