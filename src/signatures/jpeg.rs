use crate::extractors::jpeg::extract_jpeg_image;
use crate::signatures;

pub const DESCRIPTION: &str = "JPEG image";

pub fn jpeg_magic() -> Vec<Vec<u8>> {
    return vec![
        /*
         * Works for normal jpegs but not exif.
         * See: https://github.com/corkami/formats/blob/master/image/jpeg.md
         */
        b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00".to_vec(),
    ];
}

pub fn jpeg_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Perform an extraction dry-run
    let dry_run = extract_jpeg_image(file_data, offset, None);

    // If the dry-run was a success, this is probably a valid JPEG file
    if dry_run.success == true {
        // Get the total size of the JPEG
        if let Some(jpeg_size) = dry_run.size {
            // If this file, from start to finish, is just a JPEG, there's no need to extract it
            if offset == 0 && file_data.len() == jpeg_size {
                result.extraction_declined = true;
            }

            // Report signature result
            result.size = jpeg_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
