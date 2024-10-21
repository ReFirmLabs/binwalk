use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::luks::parse_luks_header;

/// Human readable description
pub const DESCRIPTION: &str = "LUKS header";

/// LUKS Headers start with these bytes
pub fn luks_magic() -> Vec<Vec<u8>> {
    vec![b"LUKS\xBA\xBE".to_vec()]
}

/// Parse and validate the LUKS header
pub fn luks_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful result
    let mut result = SignatureResult {
        offset,
        name: "luks".to_string(),
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // If the header is parsed successfully, consider it valid
    if let Ok(luks_header) = parse_luks_header(&file_data[offset..]) {
        // Version 1 and version 2 have different header fields
        if luks_header.version == 1 {
            result.description = format!(
                "{}, version: {}, cipher algorithm: {}, cipher mode: {}, hash fn: {}",
                result.description,
                luks_header.version,
                luks_header.cipher_algorithm,
                luks_header.cipher_mode,
                luks_header.hashfn
            );
        } else {
            result.description = format!(
                "{}, version: {}, header size: {} bytes, hash fn: {}",
                result.description,
                luks_header.version,
                luks_header.header_size,
                luks_header.hashfn
            );
        }

        return Ok(result);
    }

    Err(SignatureError)
}
