use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::ext::parse_ext_header;

/// Human readable description
pub const DESCRIPTION: &str = "EXT filesystem";

/// EXT magic bytes
pub fn ext_magic() -> Vec<Vec<u8>> {
    /*
     * The magic bytes for EXT are only a u16, resulting in many false positives.
     * These magic signatures include all possible values for the state and errors fields in the superblock,
     * as well as the minor version number (assumed to be 0).
     * This means fewer false positive matches, and less time spent validating false positives.
     */
    vec![
        b"\x53\xEF\x01\x00\x01\x00\x00\x00".to_vec(),
        b"\x53\xEF\x01\x00\x02\x00\x00\x00".to_vec(),
        b"\x53\xEF\x01\x00\x03\x00\x00\x00".to_vec(),
        b"\x53\xEF\x02\x00\x01\x00\x00\x00".to_vec(),
        b"\x53\xEF\x02\x00\x02\x00\x00\x00".to_vec(),
        b"\x53\xEF\x02\x00\x03\x00\x00\x00".to_vec(),
    ]
}

/// Parse the EXT signature
pub fn ext_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Offset inside the EXT image where the magic bytes reside
    const MAGIC_OFFSET: usize = 1080;

    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        offset: offset - MAGIC_OFFSET,
        size: 0,
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Some(ext_data) = file_data.get(result.offset..) {
        if let Ok(ext_header) = parse_ext_header(ext_data) {
            result.size = ext_header.image_size;
            result.description = format!("{} for {}, inodes: {}, block size: {}, block count: {}, free blocks: {}, reserved blocks: {}, total size: {} bytes", result.description,
                                                                                                                                                               ext_header.os,
                                                                                                                                                               ext_header.inodes_count,
                                                                                                                                                               ext_header.block_size,
                                                                                                                                                               ext_header.free_blocks_count,
                                                                                                                                                               ext_header.reserved_blocks_count,
                                                                                                                                                               ext_header.blocks_count,
                                                                                                                                                               result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
