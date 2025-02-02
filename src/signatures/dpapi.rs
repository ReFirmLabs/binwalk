use crate::{
    signatures::common::{SignatureError, SignatureResult},
    structures::dpapi::parse_dpapi_blob_header,
};

use super::common::CONFIDENCE_MEDIUM;

/// Human readable description
pub const DESCRIPTION: &str = "DPAPI blob data";

/// DPAPI blob data header will always start with these bytes
pub fn dpapi_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x01\x00\x00\x00\xD0\x8c\x9d\xdf\x01\x15\xd1\x11\x8c\x7a\x00\xc0\x4f\xc2\x97\xeb"
            .to_vec(),
    ]
}

/// Returns success with additional details
pub fn dpapi_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(header) = parse_dpapi_blob_header(&file_data[offset..]) {
        result.description = format!(
            "{}, header_size: {}, blob_size: {}, version: {}, provider_id: {}, master_key_version: {}, 
             master_key_id: {}, flags: {}, description_len: {}, crypto_algorithm: {}, crypti_alg_len: {}, 
             salt_len: {}, hmac_key_len: {}, hash_algorithm: {}, hash_alg_len: {}, hmac2_key_len: {}, 
             data_len: {}, sign_len: {}", 
             result.description, header.header_size, header.blob_size, header.version, header.provider_id,
             header.master_key_version, header.master_key_id, header.flags, header.description_len,
             header.crypto_algorithm, header.crypti_alg_len, header.salt_len, header.hmac_key_len,
             header.hash_algorithm, header.hash_alg_len, header.hmac2_key_len, header.data_len, header.sign_len
            );
    }

    Err(SignatureError)
}
