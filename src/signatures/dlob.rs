use crate::signatures;
use crate::structures::dlob::parse_dlob_header;

pub const DESCRIPTION: &str = "DLOB firmware header";

pub fn dlob_magic() -> Vec<Vec<u8>> {
    return vec![b"\x5e\xa3\xa4\x17".to_vec()];
}

pub fn dlob_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(dlob_header) = parse_dlob_header(&file_data[offset..]) {
        // Both parts should have the same magic bytes
        if dlob_header.magic1 == dlob_header.magic2 {
            result.size = dlob_header.size;
            result.description =
                format!("{}, header size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
