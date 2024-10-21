use crate::structures::common::{self, StructureError};

/// Struct to store RTK firmware header info
#[derive(Debug, Default, Clone)]
pub struct RTKHeader {
    pub image_size: usize,
    pub header_size: usize,
}

/// Parses a RTK header
pub fn parse_rtk_header(rtk_data: &[u8]) -> Result<RTKHeader, StructureError> {
    const MAGIC_SIZE: usize = 4;

    let rtk_structure = vec![
        ("magic", "u32"),
        ("image_size", "u32"),
        ("checksum", "u32"),
        ("unknown1", "u32"),
        ("header_size", "u32"),
        ("unknown2", "u32"),
        ("unknown3", "u32"),
        ("identifier", "u32"),
    ];

    let mut result = RTKHeader {
        ..Default::default()
    };

    // Parse the header
    if let Ok(rtk_header) = common::parse(rtk_data, &rtk_structure, "little") {
        result.image_size = rtk_header["image_size"];
        result.header_size = rtk_header["header_size"] + MAGIC_SIZE;
        return Ok(result);
    }

    Err(StructureError)
}
