use crate::signatures::common::{CONFIDENCE_LOW, SignatureError, SignatureResult};

/// Human readable description
pub const DESCRIPTION_AES_SBOX: &str = "AES S-Box";
pub const DESCRIPTION_AES_FT: &str = "AES Forward Table";
pub const DESCRIPTION_AES_RT: &str = "AES Reverse Table";
pub const DESCRIPTION_AES_RCON: &str = "AES RCON";
pub const DESCRIPTION_AES_ACC: &str = "AES Acceleration Table";

/// AES S-box magic bytes
pub fn aes_sbox_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x63\x7C\x77\x7B\xF2\x6B\x6F\xC5".to_vec(), // Forward S-Box
        b"\x52\x09\x6A\xD5\x30\x36\xA5\x38".to_vec(), // Reverse S-Box
    ]
}

pub fn aes_forward_table_magic() -> Vec<Vec<u8>> {
    vec![b"\xC6\x63\x63\xA5\xF8\x7C\x7C\x84\xEE\x77\x77\x99\xF6\x7B\x7B\x8D".to_vec()]
}

pub fn aes_reverse_table_magic() -> Vec<Vec<u8>> {
    vec![b"\x51\xF4\xA7\x50\x7E\x41\x65\x53\x1A\x17\xA4\xC3\x3A\x27\x5E\x96".to_vec()]
}

pub fn aes_rcon_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x01\x02\x04\x08\x10\x20\x40\x80\x1B\x36".to_vec(),
        b"\x01\x00\x00\x00\x02\x00\x00\x00\x04\x00\x00\x00\x08\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x40\x00\x00\x00\x80\x00\x00\x00\x1B\x00\x00\x00\x36\x00\x00\x00".to_vec(),
    ]
}

pub fn aes_acceleration_table_magic() -> Vec<Vec<u8>> {
    vec![
        b"\xA5\x84\x99\x8D\x0D\xBD\xB1\x54\x50\x03\xA9\x7D\x19\x62\xE6\x9A".to_vec(), // combined sbox x2
        b"\xC6\xF8\xEE\xF6\xFF\xD6\xDE\x91\x60\x02\xCE\x56\xE7\xB5\x4D\xEC".to_vec(), // combined sbox x3
        b"\x00\x02\x04\x06\x08\x0a\x0c\x0e\x10\x12\x14\x16\x18\x1a\x1c\x1e\x20\x22\x24\x26\x28\x2a\x2c\x2e".to_vec(),   // Gallois mult 2
        b"\x00\x03\x06\x05\x0c\x0f\x0a\x09\x18\x1b\x1e\x1d\x14\x17\x12\x11\x30\x33\x36\x35\x3c\x3f\x3a\x39".to_vec(),   // Gallois mult 3
        b"\x00\x09\x12\x1b\x24\x2d\x36\x3f\x48\x41\x5a\x53\x6c\x65\x7e\x77\x90\x99\x82\x8b\xb4\xbd\xa6\xaf".to_vec(),   // Gallois mult 9
        b"\x00\x0b\x16\x1d\x2c\x27\x3a\x31\x58\x53\x4e\x45\x74\x7f\x62\x69\xb0\xbb\xa6\xad\x9c\x97\x8a\x81".to_vec(),   // Gallois mult 11
        b"\x00\x0d\x1a\x17\x34\x39\x2e\x23\x68\x65\x72\x7f\x5c\x51\x46\x4b\xd0\xdd\xca\xc7\xe4\xe9\xfe\xf3".to_vec(),   // Gallois mult 13
        b"\x00\x0e\x1c\x12\x38\x36\x24\x2a\x70\x7e\x6c\x62\x48\x46\x54\x5a\xe0\xee\xfc\xf2\xd8\xd6\xc4\xca".to_vec(),   // Gallois mult 14
    ]
}

/// Validates the AES S-Box
pub fn aes_sbox_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION_AES_SBOX.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}

/// Validates the AES Forward Table
pub fn aes_forward_table_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION_AES_FT.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}

/// Validates the AES Reverse Table
pub fn aes_reverse_table_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION_AES_RT.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}

/// Validates the AES Acceleration Table
pub fn aes_acceleration_table_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: DESCRIPTION_AES_ACC.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}

/// Validates the AES RCON
pub fn aes_rcon_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let result = SignatureResult {
        offset,
        description: "AES RCON".to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // Nothing to do, just return success
    Ok(result)
}
