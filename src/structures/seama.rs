use crate::structures;

pub struct SeamaHeader {
    pub data_size: usize,
    pub header_size: usize,
}

pub fn parse_seama_header(seama_data: &[u8]) -> Result<SeamaHeader, structures::common::StructureError> {
    const MAGIC: usize = 0x5EA3A417;

    let seama_structure = vec![
        ("magic", "u32"),
        ("description_size", "u32"),
        ("data_size", "u32"),
        ("unknown1", "u64"),
        ("unknown2", "u64"),
    ];

    let mut endianness: &str = "little";
    let header_size: usize = structures::common::size(&seama_structure);

    // Sanity check the size of available data
    if seama_data.len() > header_size {
        // Parse the header; try little endian first
        let mut seama_header = structures::common::parse(&seama_data, &seama_structure, endianness);

        // If the magic bytes don't match, switch to big endian
        if seama_header["magic"] != MAGIC {
            endianness = "big";
            seama_header = structures::common::parse(&seama_data, &seama_structure, endianness);
        }

        // Sanity check the reported size of the firmware description string
        if seama_data.len() >= (header_size + seama_header["description_size"]) {

            return Ok(SeamaHeader {
                data_size: seama_header["data_size"],
                header_size: header_size + seama_header["description_size"],
            });
        }
    }

    return Err(structures::common::StructureError);
}
