use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::efigpt::parse_efigpt_header;

/// Human readable description
pub const DESCRIPTION: &str = "EFI Global Partition Table";

/// EFI GPT always contains these bytes
pub fn efigpt_magic() -> Vec<Vec<u8>> {
    return vec![b"\x55\xAAEFI PART".to_vec()];
}

/// Validates the EFI GPT header
pub fn efigpt_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Offset of magic bytes from the start of the MBR
    const MAGIC_OFFSET: usize = 0x01FE;

    // Successful return value
    let mut result = SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    if offset >= MAGIC_OFFSET {
        // MBR actually starts this may bytes before the magic bytes
        result.offset = offset - MAGIC_OFFSET;

        // Get the EFI data, including the MBR block
        if let Some(efi_data) = file_data.get(result.offset..) {
            // Parse the EFI data; this also validates CRC so if this succeeds, confidence is high
            if let Ok(efi_header) = parse_efigpt_header(efi_data) {
                result.size = efi_header.total_size;
                result.description = format!("{}, total size: {}", result.description, result.size);
                return Ok(result);
            }
        }
    }

    return Err(SignatureError);
}
