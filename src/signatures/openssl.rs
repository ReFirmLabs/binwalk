use crate::common::is_printable_ascii;
use crate::signatures::common::{
    CONFIDENCE_LOW, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
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
        // Sanity check the salt value
        if !is_salt_invalid(openssl_header.salt) {
            // If the magic starts at the beginning of a file, our confidence is a bit higher
            if offset == 0 {
                result.confidence = CONFIDENCE_MEDIUM;
            }

            result.description =
                format!("{}, salt: {:#X}", result.description, openssl_header.salt);
            return Ok(result);
        }
    }

    Err(SignatureError)
}

// Returns true if the salt is entirely comprised of NULL and/or ASCII bytes
fn is_salt_invalid(salt: usize) -> bool {
    const SALT_LEN: usize = 8;

    let mut bad_byte_count: usize = 0;

    for i in 0..SALT_LEN {
        let salt_byte = ((salt >> (8 * i)) & 0xFF) as u8;

        if salt_byte == 0 || is_printable_ascii(salt_byte) {
            bad_byte_count += 1;
        }
    }

    bad_byte_count == SALT_LEN
}
