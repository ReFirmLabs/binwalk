use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::ntfs::parse_ntfs_header;

/// Human readable description
pub const DESCRIPTION: &str = "NTFS partition";

/// NTFS partitions start with these bytes
pub fn ntfs_magic() -> Vec<Vec<u8>> {
    vec![b"\xEb\x52\x90NTFS\x20\x20\x20\x20".to_vec()]
}

/// Validates the NTFS header
pub fn ntfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(ntfs_header) = parse_ntfs_header(&file_data[offset..]) {
        // The reported sector count does not include the NTFS boot sector itself
        result.size = ntfs_header.sector_size * (ntfs_header.sector_count + 1);

        // Simple sanity check on the reported total size
        if result.size > ntfs_header.sector_size {
            result.description = format!(
                "{}, number of sectors: {}, bytes per sector: {}, total size: {} bytes",
                result.description, ntfs_header.sector_count, ntfs_header.sector_size, result.size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
