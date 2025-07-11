use crate::extractors::bmp::extract_bmp_image;
use crate::signatures::common::{CONFIDENCE_MEDIUM, SignatureError, SignatureResult};

/// Human readable description
pub const DESCRIPTION: &str = "BMP image (Bitmap)";

// BMPs start with these bytes
// https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapfileheader
// "The file type; must be 0x4d42 (the ASCII string "BM")"
pub fn bmp_magic() -> Vec<Vec<u8>> {
    vec![b"BM".to_vec()]
}

// Validates BMP header
pub fn bmp_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        name: "bmp".to_string(),
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Extraction dry-run to validate the image
    let dry_run = extract_bmp_image(file_data, offset, None);

    // If it was successful, inform the user
    if dry_run.success {
        // Retrieve total file size and report it to the user
        if let Some(total_size) = dry_run.size {
            result.description = format!("BMP image, total size: {total_size}");
            result.size = total_size;
            return Ok(result);
        }
    }

    Err(SignatureError)
}
