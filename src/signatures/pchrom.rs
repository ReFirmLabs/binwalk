use crate::signatures::common::{SignatureError, SignatureResult};
use crate::structures::pchrom::parse_pchrom_header;

/// Human readable description
pub const DESCRIPTION: &str = "Intel serial flash for PCH ROM";

/// PCH ROM magic bytes
pub fn pch_rom_magic() -> Vec<Vec<u8>> {
    vec![b"\x5a\xa5\xf0\x0f".to_vec()]
}

/// Validate a PCH ROM signature
pub fn pch_rom_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Magic bytes begin at this offset from the start of file
    const MAGIC_OFFSET: usize = 16;

    let mut result = SignatureResult {
        size: 0,
        offset: 0,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    // Sanity check the offset where the magic bytes were found
    if offset >= MAGIC_OFFSET {
        // Set the reported starting offset of this signature
        result.offset = offset - MAGIC_OFFSET;

        // Parse the header; if this succeeds, assume it is valid
        if let Ok(pchrom_header) = parse_pchrom_header(&file_data[result.offset..]) {
            result.size = pchrom_header.header_size + pchrom_header.data_size;
            return Ok(result);
        }
    }

    Err(SignatureError)
}
