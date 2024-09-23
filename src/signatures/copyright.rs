use crate::common::get_cstring;
use crate::signatures;

pub const DESCRIPTION: &str = "Copyright text";

pub fn copyright_magic() -> Vec<Vec<u8>> {
    return vec![
        b"copyright".to_vec(),
        b"Copyright".to_vec(),
        b"COPYRIGHT".to_vec(),
    ];
}

pub fn copyright_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const MAGIC_SIZE: usize = 9;

    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    let copyright_string = get_cstring(&file_data[offset..]);

    if copyright_string.len() > MAGIC_SIZE {
        result.size = copyright_string.len();
        // Truncate copright text to 100 bytes
        result.description = format!("{}: \"{:.100}\"", result.description, copyright_string);
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
