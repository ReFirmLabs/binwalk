use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};

/// Human readable description
pub const DESCRIPTION: &str = "compress'd data";

/// Compress'd files always start with these bytes
pub fn compressd_magic() -> Vec<Vec<u8>> {
    vec![b"\x1F\x9D\x90".to_vec()]
}

/// "Validate" the compress'd header
pub fn compressd_parser(
    _file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value; confidence is medium since this only matches magic bytes at the beginning of a file
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if offset == 0 {
        result.confidence = CONFIDENCE_MEDIUM;
    }

    Ok(result)
}
