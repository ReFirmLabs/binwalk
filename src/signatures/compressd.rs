use crate::signatures;

pub const DESCRIPTION: &str = "compress'd data";

pub fn compressd_magic() -> Vec<Vec<u8>> {
    return vec![b"\x1F\x9D\x90".to_vec()];
}

pub fn compressd_parser(
    _file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // This is enforced in magic.rs so this check is superfluous
    if offset == 0 {
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
