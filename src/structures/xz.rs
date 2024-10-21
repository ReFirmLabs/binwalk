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

/// Parse and validate an XZ footer, returns the footer size
pub fn parse_xz_footer(xz_data: &[u8]) -> Result<usize, StructureError> {
    const FOOTER_SIZE: usize = 12;
    const CRC_DATA_SIZE: usize = 6;
    const CRC_START_INDEX: usize = 4;

    let xz_footer_structure = vec![
        ("footer_crc", "u32"),
        ("backward_size", "u32"),
        ("flags", "u16"),
        ("magic", "u16"),
    ];

    // Parse the stream footer
    if let Ok(xz_footer) = common::parse(xz_data, &xz_footer_structure, "little") {
        // Calculate the start and end offsets of the CRC'd data
        let crc_start = CRC_START_INDEX;
        let crc_end = crc_start + CRC_DATA_SIZE;

        // Validate the stream footer
        if let Some(crc_data) = xz_data.get(crc_start..crc_end) {
            if crc32(crc_data) == (xz_footer["footer_crc"] as u32) {
                return Ok(FOOTER_SIZE);
            }
        }
    }

    Err(StructureError)
}
