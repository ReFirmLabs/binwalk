use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use crate::structures::openssl::parse_openssl_crypt_header;

/// Human readable description
pub const DESCRIPTION: &str = "OpenSSL encryption";

/// OpenSSL crypto magic
pub fn openssl_crypt_magic() -> Vec<Vec<u8>> {
    vec![b"Salted__".to_vec()]
}

/// Validate an openssl signature
pub fn openssl_crypt_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Parse the header
    if let Ok(openssl_header) = parse_openssl_crypt_header(&file_data[offset..]) {
        // If the magic starts at the beginning of a file, our confidence is a bit higher
        if offset == 0 {
            result.confidence = CONFIDENCE_MEDIUM;
        }

        result.description = format!("{}, salt: {:#X}", result.description, openssl_header.salt);
        return Ok(result);
    }

    Err(SignatureError)
}
