use crate::signatures::common::{
    CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};

use crate::extractors::dex::extract_dex_file;

pub const DESCRIPTION: &str = "DEX file (Dalvik Executable)";

/// DEX files start with "dex\n"
pub fn dex_magic() -> Vec<Vec<u8>> {
    vec![b"dex\n".to_vec()]
}

/// Validates the DEX header
pub fn dex_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {

    let mut result = SignatureResult {
        offset,
        name: "dex".to_string(),
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    let dry_run = extract_dex_file(file_data, offset, None);

    if dry_run.success {
        // Retrieve total file size and report it
        if let Some(total_size) = dry_run.size {
            result.description = format!("DEX file, total size: {total_size}");
            result.size = total_size;
            return Ok(result);
        }
    }

    Err(SignatureError)
}