use crate::structures::common::{self, StructureError};

/// Struct to store DLOB header info
#[derive(Debug, Default, Clone)]
pub struct DlobHeader {
    pub data_size: usize,
    pub header_size: usize,
}

/// Parses a DLOB header
pub fn parse_dlob_header(dlob_data: &[u8]) -> Result<DlobHeader, StructureError> {
    let dlob_structure_p1 = vec![
        ("magic", "u32"),
        ("metadata_size", "u32"),
        ("data_size", "u32"),
    ];

    let dlob_structure_p2 = vec![
        ("magic", "u32"),
        ("metadata_size", "u32"),
        ("data_size", "u32"),
        ("unknown", "u64"),
        ("unknown", "u64"),
    ];

    // Parse the first half of the header
    if let Ok(dlob_header_p1) = common::parse(dlob_data, &dlob_structure_p1, "big") {
        // Calculate the offset to the second part of the header
        let dlob_header_p2_offset: usize =
            common::size(&dlob_structure_p1) + dlob_header_p1["metadata_size"];

        // It is expected that the first header is metadata only
        if dlob_header_p1["data_size"] == 0 {
            // Parse the second part of the header
            if let Some(header_p2_data) = dlob_data.get(dlob_header_p2_offset..) {
                if let Ok(dlob_header_p2) = common::parse(header_p2_data, &dlob_structure_p2, "big")
                {
                    // Both parts should have the same magic bytes
                    if dlob_header_p1["magic"] == dlob_header_p2["magic"] {
                        // Calculate total header size
                        let header_total_size: usize = dlob_header_p2_offset
                            + common::size(&dlob_structure_p2)
                            + dlob_header_p2["metadata_size"];

                        // Basic sanity check on the reported data size vs header size
                        if header_total_size < dlob_header_p2["data_size"] {
                            return Ok(DlobHeader {
                                header_size: header_total_size,
                                data_size: dlob_header_p2["data_size"],
                            });
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
