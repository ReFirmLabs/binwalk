use crate::common::get_cstring;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};

/// Human readable description
pub const DESCRIPTION: &str = "HP Printer Job Language data";

/// PJL files typically start with these bytes
pub fn pjl_magic() -> Vec<Vec<u8>> {
    vec![b"\x1B%-12345X@PJL".to_vec()]
}

/// Parses display info for the PJL
pub fn pjl_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Offset to the first "@PJL" string
    const PJL_COMMANDS_OFFSET: usize = 9;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Get the PJL string data
    if let Some(pjl_command_data) = file_data.get(offset + PJL_COMMANDS_OFFSET..) {
        // Pull out a NULL terminated string
        let mut pjl_text = get_cstring(pjl_command_data);
        result.size = pjl_text.len();

        if result.size > 0 {
            // For display, replace new line and carriage return characters with spaces
            pjl_text = pjl_text.replace("\r", " ").replace("\n", "");
            result.description = format!("{}: \"{}\"", result.description, pjl_text);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
