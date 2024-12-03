use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use std::collections::HashMap;

/// Known encrypted firmware magics and their associated make/model
fn encfw_known_firmware() -> HashMap<Vec<u8>, String> {
    HashMap::from([
        (
            b"\xdf\x8c\x39\x0d".to_vec(),
            "D-Link DIR-822 rev C".to_string(),
        ),
        (b"\x35\x66\x6f\x68".to_vec(), "D-Link DAP-1665".to_string()),
        (
            b"\xf5\x2a\xa0\xb4".to_vec(),
            "D-Link DIR-842 rev C".to_string(),
        ),
        (
            b"\xe3\x13\x00\x5b".to_vec(),
            "D-Link DIR-850 rev A".to_string(),
        ),
        (
            b"\x0a\x14\xe4\x24".to_vec(),
            "D-Link DIR-850 rev B".to_string(),
        ),
    ])
}

/// Human readable description
pub const DESCRIPTION: &str = "Known encrypted firmware";

/// Known encrypted firmware magic bytes
pub fn encfw_magic() -> Vec<Vec<u8>> {
    encfw_known_firmware().keys().cloned().collect()
}

/// Parse the magic signature match
pub fn encfw_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const MAGIC_LEN: usize = 4;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Some(magic_bytes) = file_data.get(offset..offset + MAGIC_LEN) {
        if encfw_known_firmware().contains_key(magic_bytes) {
            if result.offset != 0 {
                result.confidence = CONFIDENCE_LOW;
            }

            result.description = format!(
                "{}, {}",
                result.description,
                encfw_known_firmware()[magic_bytes]
            );

            return Ok(result);
        }
    }

    Err(SignatureError)
}
