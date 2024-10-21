use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::chk::parse_chk_header;

/// Human readable description
pub const DESCRIPTION: &str = "CHK firmware header";

/// CHK firmware always start with these bytes
pub fn chk_magic() -> Vec<Vec<u8>> {
    vec![b"\x2A\x23\x24\x5E".to_vec()]
}

/// Parse and validate CHK headers
pub fn chk_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Parse the CHK header
    if let Ok(chk_header) = parse_chk_header(&file_data[offset..]) {
        // Calculate reported image size and size of available data
        let available_data: usize = file_data.len() - offset;
        let image_total_size: usize =
            chk_header.header_size + chk_header.kernel_size + chk_header.rootfs_size;

        // Total reported image size should be between the header size and the file size
        if available_data >= image_total_size && image_total_size > chk_header.header_size {
            // Report the size of the header and a brief description
            result.size = chk_header.header_size;
            result.description = format!(
                "{}, board ID: {}, header size: {} bytes, data size: {} bytes",
                result.description,
                chk_header.board_id,
                chk_header.header_size,
                chk_header.kernel_size + chk_header.rootfs_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
