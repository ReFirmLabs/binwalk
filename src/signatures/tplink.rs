use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::tplink::parse_tplink_header;

/// Human readable description
pub const DESCRIPTION: &str = "TP-Link firmware header";

/// TP-Link firmware headers start with these bytes
pub fn tplink_magic() -> Vec<Vec<u8>> {
    return vec![b"\x01\x00\x00\x00TP-LINK Technologies\x00\x00\x00\x00ver. 1.0".to_vec()];
}

/// Validates the TP-Link header
pub fn tplink_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset: offset,
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

    return Err(SignatureError);
}
