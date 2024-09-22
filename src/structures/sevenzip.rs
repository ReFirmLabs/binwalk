use crate::structures;
use crate::common::crc32;

#[derive(Debug, Default, Clone)]
pub struct SevenZipHeader {
    pub header_size: usize,
    pub major_version: usize,
    pub minor_version: usize,
    pub next_header_crc: usize,
    pub next_header_size: usize,
    pub next_header_offset: usize,
}

pub fn parse_7z_header(sevenzip_data: &[u8]) -> Result<SevenZipHeader, structures::common::StructureError> {
    const SEVENZIP_CRC_START: usize = 12;
    const SEVENZIP_HEADER_SIZE: usize = 32;

    let sevenzip_structure = vec![
        ("magic_p1", "u16"),
        ("magic_p2", "u32"),
        ("major_version", "u8"),
        ("minor_version", "u8"),
        ("header_crc", "u32"),
        ("next_header_offset", "u64"),
        ("next_header_size", "u64"),
        ("next_header_crc", "u32"),
    ];

    // Sanity check on the available file data
    if sevenzip_data.len() >= SEVENZIP_HEADER_SIZE {
        // Calculate offsets of the header data used to calculate the header crc
        let crc_start: usize = SEVENZIP_CRC_START;
        let crc_end: usize = SEVENZIP_HEADER_SIZE;

        // Parse the 7zip header
        let sevenzip_header = structures::common::parse(&sevenzip_data[0..SEVENZIP_HEADER_SIZE], &sevenzip_structure, "little");

        // Validate header CRC, which is calculated over the 'next_header_offset', 'next_header_size', and 'next_header_crc' values
        if crc32(&sevenzip_data[crc_start..crc_end]) == (sevenzip_header["header_crc"] as u32) {

            return Ok(SevenZipHeader {
                header_size: SEVENZIP_HEADER_SIZE,
                major_version: sevenzip_header["major_version"],
                minor_version: sevenzip_header["minor_version"],
                next_header_crc: sevenzip_header["next_header_crc"],
                next_header_size: sevenzip_header["next_header_size"],
                next_header_offset: sevenzip_header["next_header_offset"],
            });
        }
    }

    return Err(structures::common::StructureError);
}
