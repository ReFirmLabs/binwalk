use crate::extractors::tiff::extract_tiff_image;
use crate::signatures::common::{CONFIDENCE_MEDIUM, SignatureError, SignatureResult};

/// Human readable description
pub const DESCRIPTION: &str = "TIFF image";

/// TIFF magic bytes
pub fn tiff_magic() -> Vec<Vec<u8>> {
    vec![
        // Little-endian TIFF
        b"\x49\x49\x2A\x00".to_vec(),
        // Big-endian TIFF
        b"\x4D\x4D\x00\x2A".to_vec(),
    ]
}

/// Parse a TIFF image
pub fn tiff_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Perform an extraction dry-run
    let dry_run = extract_tiff_image(file_data, offset, None);

    // If the dry-run was a success, this is probably a valid TIFF file
    if dry_run.success {
        // Get the total size of the TIFF
        if let Some(tiff_size) = dry_run.size {
            // Report signature result
            result.size = tiff_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
