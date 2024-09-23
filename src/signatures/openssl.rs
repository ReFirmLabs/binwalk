use crate::signatures;
use crate::structures::openssl::parse_openssl_crypt_header;

pub const DESCRIPTION: &str = "OpenSSL encryption";

pub fn openssl_crypt_magic() -> Vec<Vec<u8>> {
    return vec![b"Salted__".to_vec()];
}

pub fn openssl_crypt_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(openssl_header) = parse_openssl_crypt_header(&file_data[offset..]) {
        // If the magic starts at the beginning of a file, our confidence is a bit higher
        if offset == 0 {
            result.confidence = signatures::common::CONFIDENCE_MEDIUM;
        }

        result.description = format!("{}, salt: {:#X}", result.description, openssl_header.salt);
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
