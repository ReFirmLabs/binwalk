use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::rtk::parse_rtk_header;

/// Human readable description
pub const DESCRIPTION: &str = "RTK firmware header";

/// RTK firmware images always start with these bytes
pub fn rtk_magic() -> Vec<Vec<u8>> {
    vec![b"RTK0".to_vec()]
}

/// Validates the RTK header
pub fn rtk_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Note: magic.rs enforces short=true for this signature, so offset will always be 0
    let available_data = file_data.len() - offset;

    if let Ok(rtk_header) = parse_rtk_header(&file_data[offset..]) {
        // This firmware header is expected to encompass the entirety of the remaining file data
        if rtk_header.image_size == available_data {
            result.size = rtk_header.header_size;
            result.description = format!(
                "{}, header size: {} bytes, image size: {}",
                result.description, rtk_header.header_size, rtk_header.image_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
