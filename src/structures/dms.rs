use crate::structures::common::{self, StructureError};

/// Struct to store DMS header info
#[derive(Debug, Default, Clone)]
pub struct DMSHeader {
    pub image_size: usize,
}

/// Parses a DMS header
pub fn parse_dms_header(dms_data: &[u8]) -> Result<DMSHeader, StructureError> {
    const MAGIC_P1: usize = 0x4D47;
    const MAGIC_P2: usize = 0x3C31303E;

    let dms_structure = vec![
        ("unknown1", "u16"),
        ("magic_p1", "u16"),
        ("magic_p2", "u32"),
        ("unknown2", "u32"),
        ("image_size", "u32"),
    ];

    // Parse the first half of the header
    if let Ok(dms_header) = common::parse(dms_data, &dms_structure, "big") {
        if dms_header["magic_p1"] == MAGIC_P1 && dms_header["magic_p2"] == MAGIC_P2 {
            return Ok(DMSHeader {
                image_size: dms_header["image_size"],
            });
        }
    }

    Err(StructureError)
}
