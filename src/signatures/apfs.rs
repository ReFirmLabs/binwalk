use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_LOW};
use crate::structures::apfs::{parse_apfs_header, MAGIC_OFFSET};

/// Human readable description
pub const DESCRIPTION: &str = "ApPle File System";

/// APFS magic bytes
pub fn apfs_magic() -> Vec<Vec<u8>> {
    vec![b"NXSB".to_vec()]
}

/// Validates the APFS header
pub fn apfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if offset >= MAGIC_OFFSET {
        result.offset = offset - MAGIC_OFFSET;

        if let Ok(apfs_header) = parse_apfs_header(&file_data[result.offset..]) {
            result.size = apfs_header.block_count * apfs_header.block_size;
            result.description = format!(
                "{}, block size: {} bytes, block count: {}, total size: {} bytes",
                result.description, apfs_header.block_size, apfs_header.block_count, result.size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
