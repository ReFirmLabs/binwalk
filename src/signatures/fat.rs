use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::fat::parse_fat_header;

/// Human readable description
pub const DESCRIPTION: &str = "FAT file system";

/// Offset of magic bytes from the start of the FAT
pub const MAGIC_OFFSET: usize = 0x01FE;

/// FAT always contains these bytes
pub fn fat_magic() -> Vec<Vec<u8>> {
    vec![b"\x55\xAA".to_vec()]
}

/// Validates the FAT header
pub fn fat_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Sanity check the magic offset
    if offset >= MAGIC_OFFSET {
        // FAT actually starts this may bytes before the magic bytes
        result.offset = offset - MAGIC_OFFSET;

        // Parse and validate the FAT header
        if let Some(fat_data) = file_data.get(result.offset..) {
            if let Ok(fat_header) = parse_fat_header(fat_data) {
                // Report the total size of the FAT image
                result.size = fat_header.total_size;

                // Include FAT type in the description
                let mut fat_type_desc: &str = "FAT12/16";
                if fat_header.is_fat32 {
                    fat_type_desc = "FAT32";
                }

                result.description = format!(
                    "{}, type: {}, total size: {} bytes",
                    result.description, fat_type_desc, result.size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
