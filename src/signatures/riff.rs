use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::riff::parse_riff_header;

/// Human readable description
pub const DESCRIPTION: &str = "RIFF image";

/// RIFF file magic bytes
pub fn riff_magic() -> Vec<Vec<u8>> {
    vec![b"RIFF".to_vec()]
}

/// Validate RIFF signatures
pub fn riff_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Parse the RIFF header
    if let Ok(riff_header) = parse_riff_header(&file_data[offset..]) {
        // No sense in extracting an image if the entire file is just the image itself
        if offset == 0 && riff_header.size == file_data.len() {
            result.extraction_declined = true;
        }

        result.size = riff_header.size;
        result.description = format!(
            "{}, encoding type: {}, total size: {} bytes",
            result.description, riff_header.chunk_type, result.size
        );
        return Ok(result);
    }

    Err(SignatureError)
}
