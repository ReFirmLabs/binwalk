use crate::structures::common::{self, StructureError};

/// Struct to store DLOB header info
pub struct DlobHeader {
    pub size: usize,
}

/// Parses a DLOG header
pub fn parse_dlob_header(dlob_data: &[u8]) -> Result<DlobHeader, StructureError> {
    // Expected file offsets & sizes
    const DLOB_HEADER_SIZE: usize = 108;
    const DLOB_METADATA_OFFSET: usize = 12;

    let dlob_structure = vec![
        ("magic", "u32"),
        ("metadata_size", "u32"),
        ("unknown", "u32"),
    ];

    // Parse the first half of the header
    if let Ok(dlob_header_p1) = common::parse(dlob_data, &dlob_structure, "big") {
        // Calculate the offset to the second part of the header
        let dlob_header_p2_offset: usize = dlob_header_p1["metadata_size"] + DLOB_METADATA_OFFSET;

        // Parse the second part of the header
        if let Some(header_p2_data) = dlob_data.get(dlob_header_p2_offset..) {
            if let Ok(dlob_header_p2) = common::parse(header_p2_data, &dlob_structure, "big") {
                // Both parts should have the same magic bytes
                if dlob_header_p1["magic"] == dlob_header_p2["magic"] {
                    return Ok(DlobHeader {
                        size: DLOB_HEADER_SIZE,
                    });
                }
            }
        }
    }

    return Err(StructureError);
}
