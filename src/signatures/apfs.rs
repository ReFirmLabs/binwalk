use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::apfs::{parse_apfs_header, MAGIC_OFFSET};

/// Human readable description
pub const DESCRIPTION: &str = "APple File System";

/// APFS magic bytes
pub fn apfs_magic() -> Vec<Vec<u8>> {
    vec![b"NXSB".to_vec()]
}

/// Validates the APFS header
pub fn apfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const MBR_BLOCK_SIZE: usize = 512;

    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if offset >= MAGIC_OFFSET {
        result.offset = offset - MAGIC_OFFSET;
        let available_data = file_data.len() - result.offset;

        if let Ok(apfs_header) = parse_apfs_header(&file_data[result.offset..]) {
            let mut truncated_message = "".to_string();
            result.size = apfs_header.block_count * apfs_header.block_size;

            // It is observed that an APFS contained in an EFIGPT with a protective MBR includes the MBR block in its size.
            // If the APFS image is pulled out of the EFIGPT, the reported size will be 512 bytes too long, but otherwise valid.
            if result.size > available_data {
                let truncated_size = result.size - available_data;

                // If the calculated size is 512 bytes short, adjust the reported APFS size accordingly
                if truncated_size == MBR_BLOCK_SIZE {
                    result.size -= truncated_size;
                    truncated_message = format!(" (truncated by {} bytes)", truncated_size);
                }
            }

            result.description = format!(
                "{}, block size: {} bytes, block count: {}, total size: {} bytes{}",
                result.description,
                apfs_header.block_size,
                apfs_header.block_count,
                result.size,
                truncated_message
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
