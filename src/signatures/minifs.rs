/// Credit to:
/// https://arxiv.org/html/2407.05064v1
/// https://github.com/RedaOps/minifs-extractor

use crate::extractors::minifs::minifs_extractor;
use crate::signatures::common::{
    CONFIDENCE_HIGH, SignatureError, SignatureResult,
};
use crate::structures::minifs::parse_minifs_file;

/// Human readable description
pub const DESCRIPTION: &str = "MINIFS image";

/// MINIFS magic bytes
pub fn minifs_magic() -> Vec<Vec<u8>> {
    vec![
        // Standard MINI magic
        b"MINIFS\x00\x00".to_vec(),
    ]
}

/// Validates MINIFS signatures
pub fn minifs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        size: 0,
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Ok(mf) = parse_minifs_file(&file_data[offset..]) {
        result.size = mf.file_size;
        result.preferred_extractor = Some(minifs_extractor());

        result.description = format!(
            "{}, magic: {}, unk1: {}, ver: {} num_files: {} unk2: {}, name_table_size: {}",
            result.description,
            std::str::from_utf8(mf.hdr.name.to_be_bytes().as_slice()).unwrap_or("INVALID MAGIC"),
            mf.hdr.unk1,
            mf.hdr.ver,
            mf.hdr.num_files,
            mf.hdr.unk2,
            mf.hdr.name_table_size,
        );
        return Ok(result);
    }

    Err(SignatureError)
}
