use crate::structures::common::{self, StructureError};

/// Standard DEX header size, in bytes
pub const DEX_HEADER_SIZE: usize = 112;

/// Standard DEX endian tag
pub const ENDIAN_CONSTANT: u32 = 0x1234_5678;

#[derive(Debug, Default, Clone)]
pub struct DexHeader {
    pub file_size: usize,
}

/// Parses and validates a standard DEX header.
pub fn parse_dex_header(file_data: &[u8]) -> Result<DexHeader, StructureError> {

    if file_data.len() < DEX_HEADER_SIZE {
        return Err(StructureError);
    }

    // Validate the DEX magic: "dex\nNNN\0"
    if &file_data[0..4] != b"dex\n"
        || !file_data[4..7].iter().all(u8::is_ascii_digit)
        || file_data[7] != 0
    {
        return Err(StructureError);
    }

    let dex_header_structure = vec![
        ("file_size", "u32"),
        ("header_size", "u32"),
        ("endian_tag", "u32"),
    ];

    // These fields begin at offset 32 in the DEX header
    if let Ok(header) = common::parse(&file_data[32..], &dex_header_structure, "little") {

        // Validate the header size and endian tag
        if header["header_size"] != DEX_HEADER_SIZE || header["endian_tag"] != ENDIAN_CONSTANT as usize {
            return Err(StructureError);
        }

        // The declared file size must fit within available data
        if header["file_size"] < DEX_HEADER_SIZE || header["file_size"] > file_data.len() {
            return Err(StructureError);
        }

        return Ok(DexHeader {
            file_size: header["file_size"],
        });
    }

    Err(StructureError)
}