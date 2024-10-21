use crate::structures::common::{self, StructureError};

/// Struct to store DTB info
#[derive(Debug, Default, Clone)]
pub struct DTBHeader {
    pub total_size: usize,
    pub version: usize,
    pub cpu_id: usize,
    pub struct_offset: usize,
    pub strings_offset: usize,
    pub struct_size: usize,
    pub strings_size: usize,
}

/// Parse  DTB header
pub fn parse_dtb_header(dtb_data: &[u8]) -> Result<DTBHeader, StructureError> {
    // Expected version numbers
    const EXPECTED_VERSION: usize = 17;
    const EXPECTED_COMPAT_VERSION: usize = 16;

    const STRUCT_ALIGNMENT: usize = 4;
    const MEM_RESERVATION_ALIGNMENT: usize = 8;

    let dtb_structure = vec![
        ("magic", "u32"),
        ("total_size", "u32"),
        ("dt_struct_offset", "u32"),
        ("dt_strings_offset", "u32"),
        ("mem_reservation_block_offset", "u32"),
        ("version", "u32"),
        ("min_compatible_version", "u32"),
        ("cpu_id", "u32"),
        ("dt_strings_size", "u32"),
        ("dt_struct_size", "u32"),
    ];

    let dtb_structure_size = common::size(&dtb_structure);

    // Parse the header
    if let Ok(dtb_header) = common::parse(dtb_data, &dtb_structure, "big") {
        // Check the reported versioning
        if dtb_header["version"] == EXPECTED_VERSION
            && dtb_header["min_compatible_version"] == EXPECTED_COMPAT_VERSION
        {
            // Check required byte alignments for the specified offsets
            if (dtb_header["dt_struct_offset"] & STRUCT_ALIGNMENT) == 0
                && (dtb_header["mem_reservation_block_offset"] % MEM_RESERVATION_ALIGNMENT) == 0
            {
                // All offsets must start after the header structure
                if dtb_header["dt_struct_offset"] >= dtb_structure_size
                    && dtb_header["dt_strings_offset"] >= dtb_structure_size
                    && dtb_header["mem_reservation_block_offset"] >= dtb_structure_size
                {
                    return Ok(DTBHeader {
                        total_size: dtb_header["total_size"],
                        version: dtb_header["version"],
                        cpu_id: dtb_header["cpu_id"],
                        struct_offset: dtb_header["dt_struct_offset"],
                        strings_offset: dtb_header["dt_strings_offset"],
                        struct_size: dtb_header["dt_struct_size"],
                        strings_size: dtb_header["dt_strings_size"],
                    });
                }
            }
        }
    }

    Err(StructureError)
}
