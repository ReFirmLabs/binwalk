use crate::structures::common::{self, StructureError};

/// Struct to store SEAMA firmware header data
pub struct SeamaHeader {
    pub data_size: usize,
    pub header_size: usize,
}

/// Parse a SEAMA firmware header
pub fn parse_seama_header(seama_data: &[u8]) -> Result<SeamaHeader, StructureError> {
    // SEAMA magic
    const MAGIC: usize = 0x5EA3A417;

    let seama_structure = vec![
        ("magic", "u32"),
        ("description_size", "u32"),
        ("data_size", "u32"),
        ("unknown1", "u64"),
        ("unknown2", "u64"),
    ];

    let mut endianness: &str = "little";
    let available_data = seama_data.len();
    let header_size: usize = common::size(&seama_structure);

    // Parse the header; try little endian first
    if let Ok(mut seama_header) = common::parse(seama_data, &seama_structure, endianness) {
        // If the magic bytes don't match, switch to big endian
        if seama_header["magic"] != MAGIC {
            endianness = "big";
            match common::parse(seama_data, &seama_structure, endianness) {
                Err(_) => {
                    return Err(StructureError);
                }
                Ok(seama_header_be) => {
                    seama_header = seama_header_be.clone();
                }
            }
        }

        // Sanity check on magic bytes
        if seama_header["magic"] == MAGIC {
            let total_header_size = header_size + seama_header["description_size"];

            // Sanity check on total header size
            if total_header_size >= header_size && available_data >= total_header_size {
                return Ok(SeamaHeader {
                    data_size: seama_header["data_size"],
                    header_size: total_header_size,
                });
            }
        }
    }

    Err(StructureError)
}
