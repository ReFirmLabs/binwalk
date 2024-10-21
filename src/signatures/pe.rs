use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::pe::parse_pe_header;

/// Human readable description
pub const DESCRIPTION: &str = "Windows PE binary";

/// Common PE file magics
pub fn pe_magic() -> Vec<Vec<u8>> {
    /*
     * This matches the first 16 bytes of a DOS header, from e_magic through e_ss.
     * Note that these values may differ in some special cases, but these are common ones.
     */
    vec![
        b"\x4d\x5a\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00".to_vec(),
        b"\x4d\x5a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00".to_vec(),
    ]
}

/// Validate a PE header
pub fn pe_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Parse the PE header
    if let Ok(pe_header) = parse_pe_header(&file_data[offset..]) {
        result.description = format!(
            "{}, machine type: {}",
            result.description, pe_header.machine
        );
        return Ok(result);
    }

    Err(SignatureError)
}
