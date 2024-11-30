use crate::extractors::swapped::byte_swap;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::dms::parse_dms_header;

/// Human readable description
pub const DESCRIPTION: &str = "DMS firmware image";

/// DMS firmware image magic bytes
pub fn dms_magic() -> Vec<Vec<u8>> {
    vec![b"0><1".to_vec()]
}

/// Validates the DMS header
pub fn dms_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const MIN_SIZE: usize = 0x100;
    const BYTE_SWAP_SIZE: usize = 2;
    const MAGIC_OFFSET: usize = 4;

    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // The magic bytes start at offset 4
    if offset >= MAGIC_OFFSET {
        result.offset = offset - MAGIC_OFFSET;

        if let Some(dms_data) = file_data.get(result.offset..result.offset + MIN_SIZE) {
            // DMS firmware images have every 2 bytes swapped
            let swapped_data = byte_swap(dms_data, BYTE_SWAP_SIZE);

            // Validate the DMS firmware header
            if let Ok(dms_header) = parse_dms_header(&swapped_data) {
                result.size = dms_header.image_size;
                result.description =
                    format!("{}, total size: {} bytes", result.description, result.size);
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
