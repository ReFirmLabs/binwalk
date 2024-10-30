use crate::extractors::zlib::zlib_decompress;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "Zlib compressed file";

/// Zlib magic bytes
pub fn zlib_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x78\x9c".to_vec(),
        b"\x78\xDA".to_vec(),
        b"\x78\x5E".to_vec(),
    ]
}

/// Validate a zlib signature
pub fn zlib_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        confidence: CONFIDENCE_HIGH,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    // Decompress the zlib; no output directory specified, dry run only.
    let decompression_dry_run = zlib_decompress(file_data, offset, None);

    // If the decompression dry run was a success, this signature is almost certianly valid
    if decompression_dry_run.success {
        if let Some(zlib_file_size) = decompression_dry_run.size {
            result.size = zlib_file_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
