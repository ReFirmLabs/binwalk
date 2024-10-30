use crate::structures::common::{self, StructureError};

/// Struct to store WindowsCE header info
#[derive(Debug, Default, Clone)]
pub struct WinCEHeader {
    pub base_address: usize,
    pub image_size: usize,
    pub header_size: usize,
}

/// Parses a Windows CE header
pub fn parse_wince_header(wince_data: &[u8]) -> Result<WinCEHeader, StructureError> {
    let wince_header_structure = vec![
        ("magic_p1", "u32"),
        ("magic_p2", "u24"),
        ("image_start", "u32"),
        ("image_size", "u32"),
    ];

    // Parse the WinCE header
    if let Ok(wince_header) = common::parse(wince_data, &wince_header_structure, "little") {
        return Ok(WinCEHeader {
            base_address: wince_header["image_start"],
            image_size: wince_header["image_size"],
            header_size: common::size(&wince_header_structure),
        });
    }

    Err(StructureError)
}

/// Struct to store WindowsCE block info
#[derive(Debug, Default, Clone)]
pub struct WinCEBlock {
    pub address: usize,
    pub data_size: usize,
    pub header_size: usize,
}

/// Parse a WindowsCE block header
pub fn parse_wince_block_header(block_data: &[u8]) -> Result<WinCEBlock, StructureError> {
    let wince_block_structure = vec![("address", "u32"), ("size", "u32"), ("checksum", "u32")];

    if let Ok(block_header) = common::parse(block_data, &wince_block_structure, "little") {
        return Ok(WinCEBlock {
            address: block_header["address"],
            data_size: block_header["size"],
            header_size: common::size(&wince_block_structure),
        });
    }

    Err(StructureError)
}
