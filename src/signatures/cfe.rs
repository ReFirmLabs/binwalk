use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};

/// Human readable description
pub const DESCRIPTION: &str = "CFE bootloader";

/// CFE bootloader always contains this string
pub fn cfe_magic() -> Vec<Vec<u8>> {
    vec![b"CFE1CFE1".to_vec()]
}

/// Validate the CFE signature
pub fn cfe_parser(_file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Magic bytes occur this many bytes into the bootloader
    const CFE_MAGIC_OFFSET: usize = 28;

    // Success result; confidence is set to low by default as little additional validation is performed
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    // CFE signature must start at least CFE_MAGIC_OFFSET bytes into the file
    if offset >= CFE_MAGIC_OFFSET {
        // Adjust the reported starting offset accordingly
        result.offset = offset - CFE_MAGIC_OFFSET;

        // If this signature occurs at the very beginning of a file, our confidence is a bit higher
        if result.offset == 0 {
            result.confidence = CONFIDENCE_MEDIUM;
        }

        return Ok(result);
    }

    Err(SignatureError)
}
