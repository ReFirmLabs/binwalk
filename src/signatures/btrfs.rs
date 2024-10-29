use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::btrfs::parse_btrfs_header;

/// Human readable description
pub const DESCRIPTION: &str = "BTRFS file system";

/// BTRFS magic bytes
pub fn btrfs_magic() -> Vec<Vec<u8>> {
    vec![b"_BHRfS_M".to_vec()]
}

/// Validates the BTRFS header
pub fn btrfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Offset of the superblock magic bytes in a BTRFS image
    const MAGIC_OFFSET: usize = 0x10040;

    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Sanity check the reported offset
    if offset >= MAGIC_OFFSET {
        // Actual offset is the location of the magic bytes minus the magic byte offset
        result.offset = offset - MAGIC_OFFSET;

        // Parse the superblock header; this also validates the superblock CRC
        if let Ok(btrfs_header) = parse_btrfs_header(&file_data[result.offset..]) {
            result.size = btrfs_header.total_size;
            result.description = format!(
                "{}, node size: {}, sector size: {}, leaf size: {}, stripe size: {}, bytes used: {}, total size: {} bytes",
                result.description, btrfs_header.node_size, btrfs_header.sector_size, btrfs_header.leaf_size, btrfs_header.stripe_size, btrfs_header.bytes_used, result.size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
