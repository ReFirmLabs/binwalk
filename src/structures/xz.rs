use crate::common::crc32;
use crate::structures::common::{self, StructureError};

/// Parse and validate an XZ header, returns the header size
pub fn parse_xz_header(xz_data: &[u8]) -> Result<usize, StructureError> {
    const XZ_CRC_END: usize = 8;
    const XZ_CRC_START: usize = 6;
    const XZ_HEADER_SIZE: usize = 12;

    let xz_structure = vec![
        ("magic_p1", "u32"),
        ("magic_p2", "u16"),
        ("flags", "u16"),
        ("header_crc", "u32"),
    ];

    if let Ok(xz_header) = common::parse(xz_data, &xz_structure, "little") {
        if let Some(crc_data) = xz_data.get(XZ_CRC_START..XZ_CRC_END) {
            if crc32(crc_data) == (xz_header["header_crc"] as u32) {
                return Ok(XZ_HEADER_SIZE);
            }
        }
    }

    Err(StructureError)
}
