use crate::extractors::gpg::gpg_decompress;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const GPG_SIGNED_DESCRIPTION: &str = "GPG signed file";

/// GPG signed files start with these two bytes
pub fn gpg_signed_magic() -> Vec<Vec<u8>> {
    vec![b"\xA3\x01".to_vec()]
}

/// Validates GPG signatures
pub fn gpg_signed_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Success result; confidence is high since this signature is only reported what it starts at the beginning of a file
    let mut result = SignatureResult {
        offset,
        confidence: CONFIDENCE_HIGH,
        description: GPG_SIGNED_DESCRIPTION.to_string(),
        ..Default::default()
    };

    /*
     * GPG signed files are just zlib compressed files with the zlib magic bytes replaced with the GPG magic bytes.
     * Decompress the signed file; no output directory specified, dry run only.
     */
    let decompression_dry_run = gpg_decompress(file_data, offset, None);

    // If the decompression dry run was a success, this signature is almost certianly valid
    if decompression_dry_run.success {
        if let Some(total_size) = decompression_dry_run.size {
            result.size = total_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
