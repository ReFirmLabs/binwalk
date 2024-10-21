use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::common;
use std::collections::HashMap;

/// Human readable description
pub const DESCRIPTION: &str = "RSA encrypted session key";

/// Stores defintions about each RSA key type
#[derive(Debug, Default, Clone)]
struct RSAKeyDefinition {
    // Magic bytes for this RSA key
    pub magic: Vec<u8>,
    // Size of the RSA key, in bits
    pub key_size: usize,
    // Offset of the byte indicating if the key can be used for signing/encryption
    pub usage_offset: usize,
    // Offset of the 64-bit key ID
    pub keyid_offset: usize,
    // HashMap of offsets and expected bytes
    pub valid_checks: HashMap<usize, Vec<Vec<u8>>>,
    // Offset of the expected terminator byte, 0xD2
    pub terminator_offset: usize,
}

/// Returns a list of RSA key definitions
fn rsa_key_definitions() -> Vec<RSAKeyDefinition> {
    vec![
        // 1024b RSA key
        RSAKeyDefinition {
            magic: b"\x84\x8C\x03".to_vec(),
            key_size: 1024,
            keyid_offset: 3,
            terminator_offset: 142,
            usage_offset: 11,
            valid_checks: HashMap::from([(
                12,
                vec![
                    b"\x04\x00".to_vec(),
                    b"\x03\xff".to_vec(),
                    b"\x03\xfe".to_vec(),
                    b"\x03\xfd".to_vec(),
                    b"\x03\xfc".to_vec(),
                    b"\x03\xfb".to_vec(),
                    b"\x03\xfa".to_vec(),
                    b"\x03\xf9".to_vec(),
                ],
            )]),
        },
        // 2048b RSA key
        RSAKeyDefinition {
            magic: b"\x85\x01\x0c\x03".to_vec(),
            key_size: 2048,
            keyid_offset: 4,
            terminator_offset: 271,
            usage_offset: 12,
            valid_checks: HashMap::from([(
                13,
                vec![
                    b"\x08\x00".to_vec(),
                    b"\x07\xff".to_vec(),
                    b"\x07\xfe".to_vec(),
                    b"\x07\xfd".to_vec(),
                    b"\x07\xfc".to_vec(),
                    b"\x07\xfb".to_vec(),
                    b"\x07\xfa".to_vec(),
                    b"\x07\xf9".to_vec(),
                ],
            )]),
        },
        // 3072b RSA key
        RSAKeyDefinition {
            magic: b"\x85\x01\x8c\x03".to_vec(),
            key_size: 3072,
            keyid_offset: 4,
            terminator_offset: 399,
            usage_offset: 12,
            valid_checks: HashMap::from([(
                13,
                vec![
                    b"\x0c\x00".to_vec(),
                    b"\x0b\xff".to_vec(),
                    b"\x0b\xfe".to_vec(),
                    b"\x0b\xfd".to_vec(),
                    b"\x0b\xfc".to_vec(),
                    b"\x0b\xfb".to_vec(),
                    b"\x0b\xfa".to_vec(),
                    b"\x0b\xf9".to_vec(),
                ],
            )]),
        },
        // 4096b RSA key
        RSAKeyDefinition {
            magic: b"\x85\x02\x0c\x03".to_vec(),
            key_size: 4096,
            keyid_offset: 4,
            terminator_offset: 527,
            usage_offset: 12,
            valid_checks: HashMap::from([(
                13,
                vec![
                    b"\x10\x00".to_vec(),
                    b"\x0f\xff".to_vec(),
                    b"\x0f\xfe".to_vec(),
                    b"\x0f\xfd".to_vec(),
                    b"\x0f\xfc".to_vec(),
                    b"\x0f\xfb".to_vec(),
                    b"\x0f\xfa".to_vec(),
                    b"\x0f\xf9".to_vec(),
                ],
            )]),
        },
        // 8192b RSA key
        RSAKeyDefinition {
            magic: b"\x85\x04\x0c\x03".to_vec(),
            key_size: 8192,
            keyid_offset: 4,
            terminator_offset: 1039,
            usage_offset: 12,
            valid_checks: HashMap::from([(
                13,
                vec![
                    b"\x20\x00".to_vec(),
                    b"\x1f\xff".to_vec(),
                    b"\x1f\xfe".to_vec(),
                    b"\x1f\xfd".to_vec(),
                    b"\x1f\xfc".to_vec(),
                    b"\x1f\xfb".to_vec(),
                    b"\x1f\xfa".to_vec(),
                    b"\x1f\xf9".to_vec(),
                ],
            )]),
        },
    ]
}

/// RSA crypto magic bytes
pub fn rsa_magic() -> Vec<Vec<u8>> {
    let mut magics: Vec<Vec<u8>> = vec![];

    for key_definition in rsa_key_definitions() {
        magics.push(key_definition.magic.clone());
    }

    magics
}

/// Validates an RSA encrypted file header
pub fn rsa_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Loop through all the known RSA key types
    for key_definition in rsa_key_definitions() {
        let magic_start: usize = offset;
        let magic_end: usize = magic_start + key_definition.magic.len();

        // Check if these magic bytes belong to this key type
        if let Some(rsa_magic) = file_data.get(magic_start..magic_end) {
            if rsa_magic == key_definition.magic {
                // Parse and validate the key data
                match rsa_key_parser(&file_data[magic_start..], &key_definition) {
                    Err(_) => {
                        break;
                    }
                    Ok(key_info) => {
                        result.size = key_info.data_size;
                        result.description = format!(
                            "{}, {} bits, can sign: {}, can encrypt: {}, key ID: {:#018X}",
                            result.description,
                            key_info.bits,
                            key_info.can_sign,
                            key_info.can_encrypt,
                            key_info.key_id
                        );
                        return Ok(result);
                    }
                }
            }
        }
    }

    Err(SignatureError)
}

/// Stores info about a validated RSA key
#[derive(Debug, Default, Clone)]
struct RSAKeyInfo {
    pub bits: usize,
    pub can_sign: bool,
    pub can_encrypt: bool,
    pub key_id: usize,
    pub data_size: usize,
}

/// Parse and validate key data based on the provided key definition
fn rsa_key_parser(
    raw_data: &[u8],
    key_definition: &RSAKeyDefinition,
) -> Result<RSAKeyInfo, SignatureError> {
    // Expected constant values
    const TERMINATOR_BYTE: u8 = 0xD2;
    const ENCRYPT_ONLY: u8 = 2;
    const SIGN_AND_ENCRYPT: u8 = 1;
    const VALID_BYTES_SIZE: usize = 2;

    let key_id_structure = vec![("id", "u64")];

    let mut result = RSAKeyInfo {
        ..Default::default()
    };

    // This is the farthest offset we'll need to index into the key data
    let key_data_len: usize = key_definition.terminator_offset + std::mem::size_of::<u8>();

    if let Some(key_data) = raw_data.get(0..key_data_len) {
        // Check the terminator byte
        if key_data[key_definition.terminator_offset] == TERMINATOR_BYTE {
            // Get the key ID
            if let Ok(key_id) = common::parse(
                &key_data[key_definition.keyid_offset..],
                &key_id_structure,
                "big",
            ) {
                // Report the key ID
                result.key_id = key_id["id"];

                // Determine if this key can be used to sign or encrypt
                result.can_encrypt = key_data[key_definition.usage_offset] == ENCRYPT_ONLY;
                result.can_sign = key_data[key_definition.usage_offset] == SIGN_AND_ENCRYPT;

                // If a key can sign, it can also encrypt
                if result.can_sign {
                    result.can_encrypt = true;
                }

                // A key that can't sign or encrypt would be useless!
                if result.can_sign || result.can_encrypt {
                    // Each key has a set of fixed-size bytes that are expected to exist at certian offsets
                    for (valid_bytes_start, valid_bytes) in
                        key_definition.valid_checks.clone().into_iter()
                    {
                        // Get the bytes to validate; always a size of 2
                        let valid_bytes_end: usize = valid_bytes_start + VALID_BYTES_SIZE;
                        let key_bytes = key_data[valid_bytes_start..valid_bytes_end].to_vec();

                        // Check the bytes in the key data against the list of expected bytes
                        for expected_bytes in valid_bytes {
                            // Got 'em!
                            if key_bytes == expected_bytes {
                                result.bits = key_definition.key_size;
                                result.data_size = key_data_len;
                                return Ok(result);
                            }
                        }
                    }
                }
            }
        }
    }

    Err(SignatureError)
}
