use crate::extractors::romfs::extract_romfs;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::romfs::parse_romfs_header;

/// Human readable description
pub const DESCRIPTION: &str = "RomFS filesystem";

/// ROMFS magic bytes
pub fn romfs_magic() -> Vec<Vec<u8>> {
    vec![b"-rom1fs-".to_vec()]
}

/// Validate a ROMFS signature
pub fn romfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        offset,
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do an extraction dry run
    let dry_run = extract_romfs(file_data, offset, None);

    // If the dry run was a success, everything should be good to go
    if dry_run.success {
        if let Some(romfs_size) = dry_run.size {
            // Parse the RomFS header to get the volume name
            if let Ok(romfs_header) = parse_romfs_header(&file_data[offset..]) {
                // Report the result
                result.size = romfs_size;
                result.description = format!(
                    "{}, volume name: \"{}\", total size: {} bytes",
                    result.description, romfs_header.volume_name, result.size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
