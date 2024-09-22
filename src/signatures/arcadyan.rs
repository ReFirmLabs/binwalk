use crate::signatures;
use crate::extractors::arcadyan::extract_obfuscated_lzma;

pub const DESCRIPTION: &str = "Arcadyan obfuscated LZMA";

pub fn obfuscated_lzma_magic() -> Vec<Vec<u8>> {
    return vec![b"\x00\xD5\x08\x00".to_vec()];
}

pub fn obfuscated_lzma_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const MAGIC_OFFSET: usize = 0x68;

    let mut result = signatures::common::SignatureResult {
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    if offset >= MAGIC_OFFSET {
        let start_offset: usize = offset - MAGIC_OFFSET;

        let dry_run = extract_obfuscated_lzma(file_data, start_offset, None);

        if dry_run.success == true {
            result.offset = start_offset;
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
