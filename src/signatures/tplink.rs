use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::tplink::{parse_tplink_header, parse_tplink_rtos_header};

/// Human readable description
pub const DESCRIPTION: &str = "TP-Link firmware header";

/// TP-Link firmware headers start with these bytes
pub fn tplink_magic() -> Vec<Vec<u8>> {
    vec![b"\x01\x00\x00\x00TP-LINK Technologies\x00\x00\x00\x00ver. 1.0".to_vec()]
}

/// Validates the TP-Link header
pub fn tplink_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Parse the header
    if let Ok(tplink_header) = parse_tplink_header(&file_data[offset..]) {
        // Fill in size and description
        result.size = tplink_header.header_size;
        result.description = format!(
            "{}, kernel load address: {:#X}, kernel entry point: {:#X}, header size: {} bytes",
            result.description,
            tplink_header.kernel_load_address,
            tplink_header.kernel_entry_point,
            tplink_header.header_size
        );

        return Ok(result);
    }

    Err(SignatureError)
}

/// Human readable description
pub const RTOS_DESCRIPTION: &str = "TP-Link RTOS firmware";

/// TP-Link RTOS firmware start with these magic bytes
pub fn tplink_rtos_magic() -> Vec<Vec<u8>> {
    vec![b"\x00\x14\x2F\xC0".to_vec()]
}

/// Parse and validate TP-Link RTOS firmware header
pub fn tplink_rtos_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        description: RTOS_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(fw_header) = parse_tplink_rtos_header(&file_data[offset..]) {
        result.description = format!("{}, model number: {:X}, hardware version: {:X}.{:X}, header size: {} bytes, total size: {} bytes",
            result.description,
            fw_header.model_number,
            fw_header.hardware_rev_major,
            fw_header.hardware_rev_minor,
            fw_header.header_size,
            fw_header.total_size,
        );
        return Ok(result);
    }

    Err(SignatureError)
}
