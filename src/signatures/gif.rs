use crate::extractors::gif::extract_gif_image;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::gif::parse_gif_header;

/// Human readable description
pub const DESCRIPTION: &str = "GIF image";

/// GIF images always start with these bytes
pub fn gif_magic() -> Vec<Vec<u8>> {
    // https://giflib.sourceforge.net/whatsinagif/bits_and_bytes.html
    vec![b"GIF87a".to_vec(), b"GIF89a".to_vec()]
}

/// Validates the GIF header
pub fn gif_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do an extraction dry-run to validate the GIF image
    let dry_run = extract_gif_image(file_data, offset, None);

    if dry_run.success {
        if let Some(total_size) = dry_run.size {
            // Everything looks ok, parse the GIF header to report some info to the user
            if let Ok(gif_header) = parse_gif_header(&file_data[offset..]) {
                // No sense in extracting a GIF from a file if the GIF data starts at offset 0
                if offset == 0 {
                    result.extraction_declined = true;
                }

                result.size = total_size;
                result.description = format!(
                    "{}, {}x{} pixels, total size: {} bytes",
                    result.description,
                    gif_header.image_width,
                    gif_header.image_height,
                    result.size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
