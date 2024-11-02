use crate::signatures::common::{SignatureError, SignatureResult};
use crate::signatures::zip;

/// Human readable description
pub const DESCRIPTION: &str = "Dahua ZIP archive";

/// Dahua ZIP file entry magic bytes
pub fn dahua_zip_magic() -> Vec<Vec<u8>> {
    // The first ZIP file entry in the Dahua ZIP file is has "DH" instead of "PK".
    // Otherwise, it is a normal ZIP file.
    vec![b"DH\x03\x04".to_vec()]
}

/// Validates a Dahua ZIP file entry signature
pub fn dahua_zip_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Parse & validate the Dahua ZIP file like a normal ZIP file
    if let Ok(mut result) = zip::zip_parser(file_data, offset) {
        // Replace the normal ZIP description string with our description string
        result.description = result.description.replace(zip::DESCRIPTION, DESCRIPTION);
        return Ok(result);
    }

    Err(SignatureError)
}
