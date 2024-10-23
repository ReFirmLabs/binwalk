use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::binhdr::parse_bin_header;

/// Human readable description
pub const DESCRIPTION: &str = "BIN firmware header";

/// BIN header magic bytes
pub fn bin_hdr_magic() -> Vec<Vec<u8>> {
    vec![b"U2ND".to_vec()]
}

/// Validates the BIN header
pub fn bin_hdr_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const MAGIC_OFFSET: usize = 14;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if offset >= MAGIC_OFFSET {
        result.offset = offset - MAGIC_OFFSET;

        if let Ok(bin_header) = parse_bin_header(&file_data[result.offset..]) {
            result.description = format!(
                "{}, board ID: {}, hardware revision: {}, firmware version: {}.{}",
                result.description,
                bin_header.board_id,
                bin_header.hardware_revision,
                bin_header.firmware_version_major,
                bin_header.firmware_version_minor,
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
