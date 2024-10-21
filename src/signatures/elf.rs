use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::elf::parse_elf_header;

/// Human readable description
pub const DESCRIPTION: &str = "ELF binary";

/// ELF files start with these bytes
pub fn elf_magic() -> Vec<Vec<u8>> {
    vec![b"\x7FELF".to_vec()]
}

/// Parse and validate the ELF header
pub fn elf_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful result
    let mut result = SignatureResult {
        offset,
        name: "elf".to_string(),
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // If the header is parsed successfully, consider it valid
    if let Ok(elf_header) = parse_elf_header(&file_data[offset..]) {
        result.description = format!(
            "{}, {}-bit {}, {} for {}, {} endian",
            result.description,
            elf_header.class,
            elf_header.exe_type,
            elf_header.machine,
            elf_header.osabi,
            elf_header.endianness
        );
        return Ok(result);
    }

    Err(SignatureError)
}
