use crate::signatures;
use crate::structures::riff::parse_riff_header;

pub const DESCRIPTION: &str = "RIFF image";

pub fn riff_magic() -> Vec<Vec<u8>> {
    return vec![b"RIFF".to_vec()];
}

pub fn riff_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_MEDIUM,
        ..Default::default()
    };

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

    return Err(signatures::common::SignatureError);
}
