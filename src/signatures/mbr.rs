use crate::extractors::mbr::extract_mbr_partitions;
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

    // This signature is only matched at the beginning of files (see magic.rs), so this check is not strictly necessary
    if offset == MAGIC_OFFSET {
        // MBR actually starts this may bytes before the magic bytes
        result.offset = offset - MAGIC_OFFSET;

        // Do an extraction dry run
        let dry_run = extract_mbr_partitions(file_data, result.offset, None);

        // If dry run was a success, this is likely a valid MBR
        if dry_run.success == true {
            if let Some(mbr_total_size) = dry_run.size {
                // Update reported MBR size
                result.size = mbr_total_size;

                // Parse the MBR header
                if let Ok(mbr_header) = parse_mbr_header(&file_data[result.offset..]) {
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
