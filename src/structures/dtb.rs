use crate::common::get_cstring;
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

/// Describes a DTB node entry
#[derive(Debug, Default, Clone)]
pub struct DTBNode {
    pub begin: bool,
    pub end: bool,
    pub eof: bool,
    pub nop: bool,
    pub property: bool,
    pub name: String,
    pub data: Vec<u8>,
    pub total_size: usize,
}

/// Parse a DTB node from the DTB data structure
pub fn parse_dtb_node(dtb_header: &DTBHeader, dtb_data: &[u8], node_offset: usize) -> DTBNode {
    const FDT_BEGIN_NODE: usize = 1;
    const FDT_END_NODE: usize = 2;
    const FDT_PROP: usize = 3;
    const FDT_NOP: usize = 4;
    const FDT_END: usize = 9;

    let node_token = vec![("id", "u32")];
    let node_property = vec![("data_len", "u32"), ("name_offset", "u32")];

    let mut node = DTBNode {
        ..Default::default()
    };

    if let Some(node_data) = dtb_data.get(node_offset..) {
        if let Ok(token) = common::parse(node_data, &node_token, "big") {
            // Set total node size to the size of the token entry
            node.total_size = common::size(&node_token);

            if token["id"] == FDT_END_NODE {
                node.end = true;
            } else if token["id"] == FDT_NOP {
                node.nop = true;
            } else if token["id"] == FDT_END {
                node.eof = true;
            // All other node types must include additional data, so the available data must be greater than just the token entry size
            } else if node_data.len() > node.total_size {
                if token["id"] == FDT_BEGIN_NODE {
                    // Begin nodes are immediately followed by a NULL-terminated name, padded to a 4-byte boundary if necessary
                    node.begin = true;
                    node.name = get_cstring(&node_data[node.total_size..]);
                    node.total_size += dtb_aligned(node.name.len() + 1);
                } else if token["id"] == FDT_PROP {
                    // Property tokens are followed by a property structure
                    if let Ok(property) =
                        common::parse(&node_data[node.total_size..], &node_property, "big")
                    {
                        // Update the total node size to include the property structure
                        node.total_size += common::size(&node_property);

                        // The property's data will immediately follow the property structure; property data may be NULL-padded for alignment
                        if let Some(property_data) =
                            node_data.get(node.total_size..node.total_size + property["data_len"])
                        {
                            node.data = property_data.to_vec();
                            node.total_size += dtb_aligned(node.data.len());

                            // Get the property name from the DTB strings table
                            if let Some(property_name_data) =
                                dtb_data.get(dtb_header.strings_offset + property["name_offset"]..)
                            {
                                node.name = get_cstring(property_name_data);
                                if !node.name.is_empty() {
                                    node.property = true;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    node
}

/// DTB entries must be aligned to 4-byte boundaries
fn dtb_aligned(len: usize) -> usize {
    const ALIGNMENT: usize = 4;

    let rem = len % ALIGNMENT;

    if rem == 0 {
        len
    } else {
        len + (ALIGNMENT - rem)
    }
}
