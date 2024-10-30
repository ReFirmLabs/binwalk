use crate::extractors::wince::wince_dump;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::wince::parse_wince_header;

/// Human readable description
pub const DESCRIPTION: &str = "Windows CE binary image";

/// Windows CE magic bytes
pub fn wince_magic() -> Vec<Vec<u8>> {
    vec![b"B000FF\n".to_vec()]
}

/// Validates the Windows CE header
pub fn wince_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do an extraction dry-run
    let dry_run = wince_dump(file_data, offset, None);

    if dry_run.success {
        if let Some(total_size) = dry_run.size {
            result.size = total_size;

            // Parse the WinCE header to get some useful info to display
            if let Ok(wince_header) = parse_wince_header(&file_data[offset..]) {
                result.description = format!(
                    "{}, base address: {:#X}, image size: {} bytes, file size: {} bytes",
                    result.description,
                    wince_header.base_address,
                    wince_header.image_size,
                    result.size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
