use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::iso9660::parse_iso_header;

/// Human readable description
pub const DESCRIPTION: &str = "ISO9660 primary volume";

/// ISOs start with these magic bytes
pub fn iso_magic() -> Vec<Vec<u8>> {
    vec![b"\x01CD001\x01\x00".to_vec()]
}

/// Validate ISO signatures
pub fn iso_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Offset from the beginning of the ISO image to the magic bytes
    const ISO_MAGIC_OFFSET: usize = 32768;

    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // We need at least ISO_MAGIC_OFFSET bytes to exist before the magic match offset
    if offset >= ISO_MAGIC_OFFSET {
        // Calculate the actual starting offset of the ISO
        result.offset = offset - ISO_MAGIC_OFFSET;

        // Parse the header, if parsing succeeds assume it's valid
        if let Ok(iso_header) = parse_iso_header(&file_data[result.offset..]) {
            result.size = iso_header.image_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
