use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::mbr::parse_mbr_header;

/// Human readable description
pub const DESCRIPTION: &str = "DOS Master Boot Record";

/// Offset of magic bytes from the start of the MBR
pub const MAGIC_OFFSET: usize = 0x01FE;

/// MBR always contains these bytes
pub fn mbr_magic() -> Vec<Vec<u8>> {
    return vec![b"\x55\xAA".to_vec()];
}

/// Validates the MBR header
pub fn mbr_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // This signature is only matched at the beginning of files (see magic.rs), so this check is not necessary
    if offset == MAGIC_OFFSET {
        // MBR actually starts this may bytes before the magic bytes
        result.offset = offset - MAGIC_OFFSET;

        // Grab the MBR header data
        if let Some(mbr_raw_data) = file_data.get(result.offset..) {
            // Parse the MBR partition table
            if let Ok(mbr_header) = parse_mbr_header(mbr_raw_data) {
                // There should be at least one valid partition
                if mbr_header.partitions.len() > 0 {
                    // Update the reported size
                    result.size = mbr_header.image_size;

                    // Add partition info to the description
                    for partition in &mbr_header.partitions {
                        result.description =
                            format!("{}, {} partition", result.description, partition.name);
                    }

                    // Add total size to the description
                    result.description =
                        format!("{}, image size: {} bytes", result.description, result.size);

                    // Everything looks ok
                    return Ok(result);
                }
            }
        }
    }

    return Err(SignatureError);
}
