use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::deb::parse_deb_header;

/// Human readable description
pub const DESCRIPTION: &str = "Debian package file";

/// Debian archives always start with these bytes
pub fn deb_magic() -> Vec<Vec<u8>> {
    vec![b"!<arch>\ndebian-binary\x20\x20\x20".to_vec()]
}

/// Validates debian archive signatures
pub fn deb_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the deb header
    if let Ok(deb_header) = parse_deb_header(&file_data[offset..]) {
        result.size = deb_header.file_size;

        // Make sure the reported size of the DEB file is sane
        if result.size <= (file_data.len() - offset) {
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
