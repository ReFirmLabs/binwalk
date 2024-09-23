use crate::signatures;
use crate::structures::webp::parse_webp_header;

pub const DESCRIPTION: &str = "WEBP image";

pub fn webp_magic() -> Vec<Vec<u8>> {
    return vec![b"RIFF".to_vec()];
}

pub fn webp_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    if let Ok(webp_header) = parse_webp_header(&file_data[offset..]) {

        // No sense in extracting an image if the entire file is just the image itself
        if offset == 0 && webp_header.size == file_data.len() {
            result.extraction_declined = true;
        }

        result.size = webp_header.size;
        result.description = format!("{}, encoding type: {}, image size: {} bytes", result.description, webp_header.chunk_type, result.size);
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
