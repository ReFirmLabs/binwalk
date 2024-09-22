use crate::extractors::zlib::zlib_decompress;
use crate::signatures::common::{ SignatureResult, SignatureError, CONFIDENCE_HIGH };

pub const DESCRIPTION: &str = "Zlib compressed file";

pub fn zlib_magic() -> Vec<Vec<u8>> {
    return vec![
        b"\x78\x9c".to_vec(),
        b"\x78\xDA".to_vec(),
        b"\x78\x5E".to_vec(),
    ];
}

/*
 * NOTE: The provided offset will always be 0; this is enforced by the 'short: true' specification
 *       in the magic.rs zlib signature definition.
 */
pub fn zlib_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    let result = SignatureResult {
        offset: offset,
        confidence: CONFIDENCE_HIGH,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    // Decompress the zlib; no output directory specified, dry run only.
    let decompression_dry_run = zlib_decompress(&file_data, offset, None);

    // If the decompression dry run was a success, this signature is almost certianly valid
    if decompression_dry_run.success == true {
        return Ok(result);
    }

    return Err(SignatureError);
}
