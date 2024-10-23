use crate::extractors::arcadyan::extract_obfuscated_lzma;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};

/// Human readable description
pub const DESCRIPTION: &str = "Arcadyan obfuscated LZMA";

/// Obfuscated Arcadyan LZMA magic bytes
pub fn obfuscated_lzma_magic() -> Vec<Vec<u8>> {
    vec![b"\x00\xD5\x08\x00".to_vec()]
}

/// Parses obfuscated Arcadyan LZMA data
pub fn obfuscated_lzma_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Magic bytes are 0x68 bytes into the actual file
    const MAGIC_OFFSET: usize = 0x68;

    // Success return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Sanity check on the reported offset; must be at least MAGIC_OFFSET bytes into the file
    if offset >= MAGIC_OFFSET {
        // Actual start of the Arcadyan data in the file
        let start_offset: usize = offset - MAGIC_OFFSET;

        // Do an extraction dry-run
        let dry_run = extract_obfuscated_lzma(file_data, start_offset, None);

        // If dry-run was successful, return success
        if dry_run.success {
            // Report the actual start of file data
            result.offset = start_offset;
            return Ok(result);
        }
    }

    Err(SignatureError)
}
