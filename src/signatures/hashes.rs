use crate::signatures;

const HASH_MAGIC_LEN: usize = 16;
pub const CRC32_DESCRIPTION: &str = "CRC32 polynomial table";
pub const SHA256_DESCRIPTION: &str = "SHA256 hash constants";

pub fn crc32_magic() -> Vec<Vec<u8>> {
    return vec![
            // Big endian
            b"\x00\x00\x00\x00\x77\x07\x30\x96\xEE\x0E\x61\x2C\x99\x09\x51\xBA".to_vec(),
            // Little endian
            b"\x00\x00\x00\x00\x96\x30\x07\x77\x2C\x61\x0E\xEE\xBA\x51\x09\x99".to_vec(),
    ];
}

pub fn sha256_magic() -> Vec<Vec<u8>> {
    return vec![
            // Big endian
            b"\x42\x8a\x2f\x98\x71\x37\x44\x91\xb5\xc0\xfb\xcf\xe9\xb5\xdb\xa5".to_vec(),
            // Little endian
            b"\x98\x2f\x8a\x42\x91\x44\x37\x71\xcf\xfb\xc0\xb5\xa5\xdb\xb5\xe9".to_vec(),
    ];
            
}

pub fn crc32_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let result = signatures::common::SignatureResult {
                                            description: format!("{}, {} endian", CRC32_DESCRIPTION, hash_endianess(file_data, offset, crc32_magic())),
                                            offset: offset,
                                            size: HASH_MAGIC_LEN,
                                            ..Default::default()
    };

    return Ok(result);
}

pub fn sha256_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let result = signatures::common::SignatureResult {
                                            description: format!("{}, {} endian", SHA256_DESCRIPTION, hash_endianess(file_data, offset, sha256_magic())),
                                            offset: offset,
                                            size: HASH_MAGIC_LEN,
                                            ..Default::default()
    };

    return Ok(result);
}

fn hash_endianess(file_data: &Vec<u8>, offset: usize, magics: Vec<Vec<u8>>) -> String {
    let mut endianness: String = "little".to_string();
    let this_magic = &file_data[offset..offset+HASH_MAGIC_LEN];
    
    if *this_magic == magics[0] {
        endianness = "big".to_string();
    }

    return endianness;
}
