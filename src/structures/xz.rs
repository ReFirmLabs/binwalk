use crate::structures;
use crate::common::crc32;

pub fn parse_xz_header(xz_data: &[u8]) -> Result<usize, structures::common::StructureError> {

    const XZ_CRC_END: usize = 8;
    const XZ_CRC_START: usize = 6;
    const XZ_HEADER_SIZE: usize = 12;

    let xz_structure = vec![
        ("magic_p1", "u32"),
        ("magic_p2", "u16"),
        ("flags", "u16"),
        ("header_crc", "u32"),
    ];

    if xz_data.len() >= XZ_HEADER_SIZE {
        let crc_end: usize = XZ_CRC_END;
        let crc_start: usize = XZ_CRC_START;

        let xz_header = structures::common::parse(&xz_data[0..XZ_HEADER_SIZE], &xz_structure, "little");

        if crc32(&xz_data[crc_start..crc_end]) == (xz_header["header_crc"] as u32) {
            return Ok(XZ_HEADER_SIZE);
        }
    }

    return Err(structures::common::StructureError);
}

pub fn parse_xz_footer(xz_data: &[u8]) -> Result<usize, structures::common::StructureError> {
    const FOOTER_SIZE: usize = 12;
    const CRC_DATA_SIZE: usize = 6;
    const CRC_START_INDEX: usize = 4;

    let xz_footer_structure = vec![
        ("footer_crc", "u32"),
        ("backward_size", "u32"),
        ("flags", "u16"),
        ("magic", "u16"),
    ];

    if xz_data.len() >= FOOTER_SIZE {
        // Parse the stream footer
        let xz_footer = structures::common::parse(&xz_data[0..FOOTER_SIZE], &xz_footer_structure, "little");

        // Calculate the start and end offsets of the CRC'd data
        let crc_start = CRC_START_INDEX;
        let crc_end = crc_start + CRC_DATA_SIZE;

        // Validate the stream footer
        if crc32(&xz_data[crc_start..crc_end]) == (xz_footer["footer_crc"] as u32) {
            return Ok(FOOTER_SIZE);
        }
    }

    return Err(structures::common::StructureError);
}
