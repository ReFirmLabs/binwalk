use crate::structures;

pub struct PackIMGHeader {
    pub header_size: usize,
    pub data_size: usize,
}

pub fn parse_packimg_header(
    packimg_data: &[u8],
) -> Result<PackIMGHeader, structures::common::StructureError> {
    const PACKIMG_HEADER_SIZE: usize = 32;

    let packimg_structure = vec![
        ("magic_p1", "u32"),
        ("magic_p2", "u32"),
        ("magic_p3", "u32"),
        ("padding1", "u32"),
        ("data_size", "u32"),
    ];

    // Parse the packimg header
    if let Ok(packimg_header) =
        structures::common::parse(&packimg_data, &packimg_structure, "little")
    {
        return Ok(PackIMGHeader {
            header_size: PACKIMG_HEADER_SIZE,
            data_size: packimg_header["data_size"],
        });
    }

    return Err(structures::common::StructureError);
}
