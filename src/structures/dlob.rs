use crate::structures;

pub struct DlobHeader {
    pub size: usize,
    pub magic1: usize,
    pub magic2: usize,
}

pub fn parse_dlob_header(
    dlob_data: &[u8],
) -> Result<DlobHeader, structures::common::StructureError> {
    const DLOB_HEADER_SIZE: usize = 108;
    const DLOB_METADATA_OFFSET: usize = 12;

    let dlob_structure = vec![
        ("magic", "u32"),
        ("metadata_size", "u32"),
        ("unknown", "u32"),
    ];

    // Sanity check the size of available data
    if dlob_data.len() >= DLOB_HEADER_SIZE {
        // Parse the first half of the header
        let dlob_header_p1 = structures::common::parse(&dlob_data, &dlob_structure, "big");

        // Calculate the offset to the second part of the header
        let dlob_header_p2_offset: usize = dlob_header_p1["metadata_size"] + DLOB_METADATA_OFFSET;

        // Sanity check the part 2 header offset
        if dlob_header_p2_offset < DLOB_HEADER_SIZE {
            // Parse the second part of the header
            let dlob_header_p2 = structures::common::parse(
                &dlob_data[dlob_header_p2_offset..],
                &dlob_structure,
                "big",
            );

            return Ok(DlobHeader {
                size: DLOB_HEADER_SIZE,
                magic1: dlob_header_p1["magic"],
                magic2: dlob_header_p2["magic"],
            });
        }
    }

    return Err(structures::common::StructureError);
}
