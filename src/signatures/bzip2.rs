use crate::extractors::bzip2::bzip2_decompressor;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "bzip2 compressed data";

/// Bzip2 magic bytes; includes the magic bytes, version number, block size, and compressed magic signature
pub fn bzip2_magic() -> Vec<Vec<u8>> {
    vec![
        b"BZh91AY&SY".to_vec(),
        b"BZh81AY&SY".to_vec(),
        b"BZh71AY&SY".to_vec(),
        b"BZh61AY&SY".to_vec(),
        b"BZh51AY&SY".to_vec(),
        b"BZh41AY&SY".to_vec(),
        b"BZh31AY&SY".to_vec(),
        b"BZh21AY&SY".to_vec(),
        b"BZh11AY&SY".to_vec(),
    ]
}

/// Bzip2 header parser
pub fn bzip2_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        offset,
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let dry_run = bzip2_decompressor(file_data, offset, None);

    if dry_run.success {
        if let Some(bzip2_size) = dry_run.size {
            result.size = bzip2_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
