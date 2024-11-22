use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::jboot::parse_jboot_arm_header;

/// Human readable description
pub const DESCRIPTION: &str = "DLK encrypted firmware";

/// DLKE encrypted firmware images always start with these bytes
pub fn dlke_magic() -> Vec<Vec<u8>> {
    // These magic bytes are technically the ROM-ID field of a JBOOT header
    vec![b"DLK6E8202001".to_vec(), b"DLK6E6110002".to_vec()]
}

/// Validates the DLKE header
pub fn dlke_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the first header, which describes the size of the firmware signature
    if let Ok(dlke_signature_header) = parse_jboot_arm_header(&file_data[offset..]) {
        // Second header should immediately follow the first
        if let Some(dlke_crypt_header_data) = file_data
            .get(offset + dlke_signature_header.header_size + dlke_signature_header.data_size..)
        {
            // Parse the second header, which describes the size of the encrypted data
            if let Ok(dlke_crypt_header) = parse_jboot_arm_header(dlke_crypt_header_data) {
                result.size = dlke_signature_header.header_size
                    + dlke_signature_header.data_size
                    + dlke_crypt_header.header_size
                    + dlke_crypt_header.data_size;
                result.description = format!(
                    "{}, signature size: {} bytes, encrypted data size: {} bytes",
                    result.description,
                    dlke_signature_header.data_size,
                    dlke_crypt_header.data_size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
