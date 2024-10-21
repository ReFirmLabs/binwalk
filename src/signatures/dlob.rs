use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::dlob::parse_dlob_header;

/// Human readable description
pub const DESCRIPTION: &str = "DLOB firmware header";

/// DLOB firmware images always start with these bytes
pub fn dlob_magic() -> Vec<Vec<u8>> {
    vec![b"\x5e\xa3\xa4\x17".to_vec()]
}

/// Validates the DLOB header
pub fn dlob_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    if let Ok(dlob_header) = parse_dlob_header(&file_data[offset..]) {
        // Sanity check on the total reported DLOB size
        if available_data >= (dlob_header.header_size + dlob_header.data_size) {
            // Don't skip the DLOB contents; it's mostly just a metadata header
            result.size = dlob_header.header_size;
            result.description = format!(
                "{}, header size: {} bytes, data size: {}",
                result.description, dlob_header.header_size, dlob_header.data_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
