use crate::common::{get_cstring, is_ascii_number};
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};

/// Human readable description
pub const DESCRIPTION: &str = "U-Boot version string";

/// U-Boot version number magic bytes
pub fn uboot_magic() -> Vec<Vec<u8>> {
    vec![b"U-Boot\x20".to_vec()]
}

/// Validates the U-Boot version number magic
pub fn uboot_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const NUMBER_OFFSET: usize = 7;

    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Some(expected_number_byte) = file_data.get(offset + NUMBER_OFFSET) {
        if is_ascii_number(*expected_number_byte) {
            let uboot_version_string = get_cstring(&file_data[offset + NUMBER_OFFSET..]);

            if !uboot_version_string.is_empty() {
                result.size = uboot_version_string.len();
                result.description =
                    format!("{}: {:.100}", result.description, uboot_version_string);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
