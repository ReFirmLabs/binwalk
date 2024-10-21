use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::dtb::parse_dtb_header;

/// Human readable description
pub const DESCRIPTION: &str = "Device tree blob (DTB)";

/// DTB files start with these magic bytes
pub fn dtb_magic() -> Vec<Vec<u8>> {
    vec![b"\xD0\x0D\xFE\xED".to_vec()]
}

/// Validates the DTB header
pub fn dtb_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Sucessful result
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Parse the DTB header
    if let Ok(dtb_header) = parse_dtb_header(&file_data[offset..]) {
        // Calculate the offsets of where the dt_struct and dt_strings end
        let dt_struct_end: usize = offset + dtb_header.struct_offset + dtb_header.struct_size;
        let dt_strings_end: usize = offset + dtb_header.strings_offset + dtb_header.strings_size;

        // Sanity check the dt_struct and dt_strings offsets
        if file_data.len() >= dt_struct_end && file_data.len() >= dt_strings_end {
            result.size = dtb_header.total_size;
            result.description = format!(
                "{}, version: {}, CPU ID: {}, total size: {} bytes",
                result.description, dtb_header.version, dtb_header.cpu_id, result.size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
