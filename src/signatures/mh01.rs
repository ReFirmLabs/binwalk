use crate::signatures::common::{CONFIDENCE_HIGH, SignatureError, SignatureResult};
use crate::signatures::openssl::openssl_crypt_parser;
use crate::structures::mh01::parse_mh01_header;

/// Human readable description
pub const DESCRIPTION: &str = "D-Link MH01 firmware image";

/// MH01 firmware images always start with these bytes
pub fn mh01_magic() -> Vec<Vec<u8>> {
    vec![b"MH01".to_vec()]
}

/// Validates the MH01 header
pub fn mh01_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the firmware header
    if let Ok(mh01_header) = parse_mh01_header(&file_data[offset..]) {
        // The encrypted data is expected to be in OpenSSL file format, so parse that too
        if let Some(crypt_data) = file_data.get(offset + mh01_header.encrypted_data_offset..) {
            if let Ok(openssl_signature) = openssl_crypt_parser(crypt_data, 0) {
                result.size = mh01_header.total_size;
                result.description = format!(
                    "{}, signed, encrypted with {}, IV: {}, total size: {} bytes",
                    result.description,
                    openssl_signature.description,
                    mh01_header.iv,
                    mh01_header.total_size,
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
