use crate::structures;

#[derive(Default, Debug, Clone)]
pub struct CramFSHeader {
    pub size: usize,
    pub checksum: u32,
    pub file_count: usize,
    pub endianness: String,
}

pub fn parse_cramfs_header(
    cramfs_data: &[u8],
) -> Result<CramFSHeader, structures::common::StructureError> {
    const HEADER_SIZE: usize = 48;

    const BIG_ENDIAN_MAGIC: usize = 0x453DCD28;
    const LITTLE_ENDIAN_MAGIC: usize = 0x28CD3D45;

    let allowed_magics: Vec<usize> = vec![BIG_ENDIAN_MAGIC, LITTLE_ENDIAN_MAGIC];

    let cramfs_header_structure = vec![
        ("magic", "u32"),
        ("size", "u32"),
        ("flags", "u32"),
        ("future", "u32"),
        ("signature_p1", "u64"),
        ("signature_p2", "u64"),
        ("checksum", "u32"),
        ("edition", "u32"),
        ("block_count", "u32"),
        ("file_count", "u32"),
    ];

    let mut cramfs_info = CramFSHeader {
        ..Default::default()
    };

    // Default to little endian
    cramfs_info.endianness = "little".to_string();

    // Sanity check the size available data
    if cramfs_data.len() > HEADER_SIZE {
        // Parse the CramFS header, try little endian first
        let mut cramfs_header = structures::common::parse(
            &cramfs_data[0..HEADER_SIZE],
            &cramfs_header_structure,
            &cramfs_info.endianness,
        );

        // Do the magic bytes match?
        if allowed_magics.contains(&cramfs_header["magic"]) {
            // If the magic bytes endianness don't match what's expected for little endian, switch to big endian
            if cramfs_header["magic"] == BIG_ENDIAN_MAGIC {
                cramfs_info.endianness = "big".to_string();
                cramfs_header = structures::common::parse(
                    &cramfs_data[0..HEADER_SIZE],
                    &cramfs_header_structure,
                    &cramfs_info.endianness,
                );
            }

            // Populate info about the CramFS image
            cramfs_info.size = cramfs_header["size"];
            cramfs_info.checksum = cramfs_header["checksum"] as u32;
            cramfs_info.file_count = cramfs_header["file_count"];

            return Ok(cramfs_info);
        }
    }

    return Err(structures::common::StructureError);
}
