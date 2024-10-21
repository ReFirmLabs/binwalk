use crate::common::get_cstring;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "Copyright text";

/// Magic copyright strings to search for
pub fn copyright_magic() -> Vec<Vec<u8>> {
    vec![
        b"copyright".to_vec(),
        b"Copyright".to_vec(),
        b"COPYRIGHT".to_vec(),
    ]
}

/// Parse copyright magic candidates
pub fn copyright_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Size of "copright" string
    const MAGIC_SIZE: usize = 9;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Get a NULL terminated string, starting at the "copright" text
    let copyright_string = get_cstring(&file_data[offset..]);

    // Make sure we got more than just the "copyright" string
    if copyright_string.len() > MAGIC_SIZE {
        result.size = copyright_string.len();
        // Truncate copright text to 100 bytes
        result.description = format!("{}: \"{:.100}\"", result.description, copyright_string);
        return Ok(result);
    }

    Err(SignatureError)
}
