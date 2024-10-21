use crate::signatures::common::{SignatureError, SignatureResult};
use crate::structures::packimg::parse_packimg_header;

/// Human readable description
pub const DESCRIPTION: &str = "PackImg firmware header";

/// PackIMG magic bytes
pub fn packimg_magic() -> Vec<Vec<u8>> {
    vec![b"--PaCkImGs--".to_vec()]
}

/// Parse a PackIMG signature
pub fn packimg_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    // Parse the header
    if let Ok(packimg_header) = parse_packimg_header(&file_data[offset..]) {
        // Sanity check the reported data size
        if available_data >= (packimg_header.header_size + packimg_header.data_size) {
            result.size = packimg_header.header_size;
            result.description = format!(
                "{}, header size: {} bytes, data size: {} bytes",
                result.description, packimg_header.header_size, packimg_header.data_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
