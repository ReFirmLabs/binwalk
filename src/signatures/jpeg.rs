use crate::extractors::jpeg::extract_jpeg_image;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};

/// Human readable description
pub const DESCRIPTION: &str = "JPEG image";

/// JPEG magic bytes
pub fn jpeg_magic() -> Vec<Vec<u8>> {
    vec![
        /*
         * Works for normal jpegs but not exif.
         * See: https://github.com/corkami/formats/blob/master/image/jpeg.md
         */
        b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00".to_vec(),
    ]
}

/// Parse a JPEG image
pub fn jpeg_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Perform an extraction dry-run
    let dry_run = extract_jpeg_image(file_data, offset, None);

    // If the dry-run was a success, this is probably a valid JPEG file
    if dry_run.success {
        // Get the total size of the JPEG
        if let Some(jpeg_size) = dry_run.size {
            // If the start of a file is a JPEG, there's no need to extract it
            if offset == 0 {
                result.extraction_declined = true;
            }

            // Report signature result
            result.size = jpeg_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
