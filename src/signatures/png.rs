use crate::extractors::png::extract_png_image;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "PNG image";

/// PNG magic bytes
pub fn png_magic() -> Vec<Vec<u8>> {
    /*
     * PNG magic, followed by chunk size and IHDR chunk type.
     * IHDR must be the first chunk type, and it is a fixed size of 0x0000000D bytes.
     */
    vec![b"\x89PNG\x0D\x0A\x1A\x0A\x00\x00\x00\x0DIHDR".to_vec()]
}

/// Validate a PNG signature
pub fn png_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Perform an extraction dry-run
    let dry_run = extract_png_image(file_data, offset, None);

    // If the dry-run was a success, this is almost certianly a valid PNG
    if dry_run.success {
        // Get the total size of the PNG
        if let Some(png_size) = dry_run.size {
            // If the start of a file PNG, there's no need to extract it
            if offset == 0 {
                result.extraction_declined = true;
            }

            // Report signature result
            result.size = png_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
