use crate::extractors::zlib::zlib_decompress;
use crate::signatures::common::{ SignatureResult, SignatureError, CONFIDENCE_HIGH };

pub const GPG_SIGNED_DESCRIPTION: &str = "GPG signed file";

pub fn gpg_signed_magic() -> Vec<Vec<u8>> {
    return vec![b"\xA3\x01".to_vec()];
}

/*
 * NOTE: The provided offset will always be 0; this is enforced by the 'short: true' specification
 *       in the magic.rs GPG signature definition.
 */
pub fn gpg_signed_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    let result = SignatureResult {
        offset: offset,
        confidence: CONFIDENCE_HIGH,
        description: GPG_SIGNED_DESCRIPTION.to_string(),
        ..Default::default()
    };

    /*
     * GPG signed files are just zlib compressed files with the zlib magic bytes replaced with the GPG magic bytes.
     * Decompress the signed file; no output directory specified, dry run only.
     */
    let decompression_dry_run = zlib_decompress(&file_data, offset, None);

    // If the decompression dry run was a success, this signature is almost certianly valid
    if decompression_dry_run.success == true {
        return Ok(result);
    }

    return Err(SignatureError);
}
