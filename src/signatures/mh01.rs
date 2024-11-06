use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::mh01::parse_mh01_header;

/// Human readable description
pub const DESCRIPTION: &str = "D-Link MH01 firmware image";

/// MH01 firmware images always start with these bytes
pub fn mh01_magic() -> Vec<Vec<u8>> {
    vec![b"MH01".to_vec()]
}

/// Validates the MH01 header
pub fn mh01_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(mh01_header) = parse_mh01_header(&file_data[offset..]) {
        result.size = mh01_header.header_size;
        result.description = format!(
            "{}, header size: {} bytes, data size: {} bytes, data hash: {}",
            result.description,
            mh01_header.header_size,
            mh01_header.data_size,
            mh01_header.data_hash,
        );
        return Ok(result);
    }

    Err(SignatureError)
}
