use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store Autel ECC header info
#[derive(Debug, Default, Clone)]
pub struct AutelECCHeader {
    pub data_size: usize,
    pub header_size: usize,
}

/// Parses an Autel header
pub fn parse_autel_header(autel_data: &[u8]) -> Result<AutelECCHeader, StructureError> {
    const EXPECTED_HEADER_SIZE: usize = 0x20;
    const COPYRIGHT_SIZE: usize = 16;
    const EXPECTED_COPYRIGHT_STRING: &str = "Copyright Autel";

    let autel_ecc_structure = vec![
        ("magic", "u64"),
        ("data_size", "u32"),
        ("header_size", "u32"),
        // Followed by 16-byte copyright string
    ];

    // Parse the header
    if let Ok(autel_header) = common::parse(autel_data, &autel_ecc_structure, "little") {
        // Sanity check the reported header size
        if autel_header["header_size"] == EXPECTED_HEADER_SIZE {
            let copyright_start = common::size(&autel_ecc_structure);
            let copyright_end = copyright_start + COPYRIGHT_SIZE;

            // Get the copyright string contained in the header
            if let Some(copyright_bytes) = autel_data.get(copyright_start..copyright_end) {
                let copyright_string = get_cstring(copyright_bytes);

                // Sanity check the copyright string value
                if copyright_string == EXPECTED_COPYRIGHT_STRING {
                    return Ok(AutelECCHeader {
                        data_size: autel_header["data_size"],
                        header_size: autel_header["header_size"],
                    });
                }
            }
        }
    }

    Err(StructureError)
}
