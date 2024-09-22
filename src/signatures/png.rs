use crate::signatures;
use crate::extractors::png::extract_png_image;

pub const DESCRIPTION: &str = "PNG image";

pub fn png_magic() -> Vec<Vec<u8>> {
    /*
     * PNG magic, followed by chunk size and IHDR chunk type.
     * IHDR must be the first chunk type, and it is a fixed size of 0x0000000D bytes.
     */
    return vec![b"\x89PNG\x0D\x0A\x1A\x0A\x00\x00\x00\x0DIHDR".to_vec()];
}

pub fn png_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };
    
    // Perform an extraction dry-run
    let dry_run = extract_png_image(file_data, offset, None);

    // If the dry-run was a success, this is almost certianly a valid PNG
    if dry_run.success == true {
        // Get the total size of the PNG
        if let Some(png_size) = dry_run.size {

            // If this file, from start to finish, is just a PNG, there's no need to extract it
            if offset == 0 && file_data.len() == png_size {
                result.extraction_declined = true;
            }

            // Report signature result
            result.size = png_size;
            result.description = format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
