use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Struct to store BIN header info
pub struct BINHeader {
    pub board_id: String,
    pub hardware_revision: String,
    pub firmware_version_major: usize,
    pub firmware_version_minor: usize,
}

/// Parses a BIN header
pub fn parse_bin_header(bin_hdr_data: &[u8]) -> Result<BINHeader, StructureError> {
    // The data strcuture is preceeded by a 4-byte board ID string
    const STRUCTURE_OFFSET: usize = 4;

    let bin_hdr_structure = vec![
        ("reserved1", "u32"),
        ("build_date", "u32"),
        ("firmware_version_major", "u8"),
        ("firmware_version_minor", "u8"),
        ("magic", "u32"),
        ("hardware_id", "u8"),
        ("reserved2", "u24"),
        ("reserved3", "u64"),
    ];

    let known_hardware_ids: HashMap<usize, &str> =
        HashMap::from([(0, "4702"), (1, "4712"), (2, "4712L"), (3, "4704")]);

    // Parse the header
    if let Some(structure_data) = bin_hdr_data.get(STRUCTURE_OFFSET..) {
        if let Ok(header) = common::parse(structure_data, &bin_hdr_structure, "little") {
            // Make sure the reserved fields are NULL
            if header["reserved1"] == 0 && header["reserved2"] == 0 && header["reserved3"] == 0 {
                // Make sure the reported hardware ID is valid
                if known_hardware_ids.contains_key(&header["hardware_id"]) {
                    // Get the board ID string, which immediately preceeds the data structure
                    if let Some(board_id_bytes) = bin_hdr_data.get(0..STRUCTURE_OFFSET) {
                        let board_id = get_cstring(board_id_bytes);

                        // The board ID string should be 4 bytes in length
                        if board_id.len() == STRUCTURE_OFFSET {
                            return Ok(BINHeader {
                                board_id,
                                hardware_revision: known_hardware_ids[&header["hardware_id"]]
                                    .to_string(),
                                firmware_version_major: header["firmware_version_major"],
                                firmware_version_minor: header["firmware_version_minor"],
                            });
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
