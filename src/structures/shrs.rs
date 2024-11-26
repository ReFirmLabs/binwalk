use crate::structures::common::{self, StructureError};

/// Struct to store SHRS firmware header info
#[derive(Debug, Default, Clone)]
pub struct SHRSHeader {
    pub iv: Vec<u8>,
    pub data_size: usize,
    pub header_size: usize,
}

/// Parses an SHRS header
pub fn parse_shrs_header(shrs_data: &[u8]) -> Result<SHRSHeader, StructureError> {
    const IV_START: usize = 12;
    const IV_END: usize = IV_START + 16;
    const HEADER_SIZE: usize = 0x6DC;

    let shrs_structure = vec![
        ("magic", "u32"),
        ("unknown1", "u32"),
        ("encrypted_data_size", "u32"),
        // 16-byte IV immediately follows
    ];

    // Parse the header
    if let Ok(shrs_header) = common::parse(shrs_data, &shrs_structure, "big") {
        if let Some(iv_bytes) = shrs_data.get(IV_START..IV_END) {
            return Ok(SHRSHeader {
                iv: iv_bytes.to_vec(),
                data_size: shrs_header["encrypted_data_size"],
                header_size: HEADER_SIZE,
            });
        }
    }

    Err(StructureError)
}
