use crate::extractors::csman::extract_csman_dat;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "CSman DAT file";

/// CSMAN DAT files always start with these bytes
pub fn csman_magic() -> Vec<Vec<u8>> {
    // Big and little endian magic
    vec![b"SC".to_vec(), b"CS".to_vec()]
}

/// Validates the CSMAN DAT file
pub fn csman_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let dry_run = extract_csman_dat(file_data, offset, None);

    if dry_run.success {
        if let Some(total_size) = dry_run.size {
            result.size = total_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    Err(SignatureError)
}
