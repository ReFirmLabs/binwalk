use crate::signatures::common::{CONFIDENCE_MEDIUM, SignatureError, SignatureResult};
use crate::structures::logfs::{LOGFS_MAGIC_OFFSET, parse_logfs_super_block};

/// Human readable description
pub const DESCRIPTION: &str = "LogFS file system";

/// LogFS magic bytes
pub fn logfs_magic() -> Vec<Vec<u8>> {
    vec![b"\x7A\x3A\x8E\x5C\xB9\xD5\xBF\x67".to_vec()]
}

/// Validates the LogFS super block
pub fn logfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if offset >= LOGFS_MAGIC_OFFSET {
        result.offset = offset - LOGFS_MAGIC_OFFSET;

        if let Some(logfs_sb_data) = file_data.get(result.offset..) {
            if let Ok(logfs_super_block) = parse_logfs_super_block(logfs_sb_data) {
                result.size = logfs_super_block.total_size;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
