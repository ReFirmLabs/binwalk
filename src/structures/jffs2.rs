use crate::structures::common::{self, StructureError};
use crc32_v2;

/// JFFS2 node header size
pub const JFFS2_NODE_STRUCT_SIZE: usize = 12;

/// Structure for storing useful JFFS node info
#[derive(Debug, Default, Clone)]
pub struct JFFS2Node {
    pub size: usize,
    pub node_type: u16,
    pub endianness: String,
}

/// Parse a JFFS2 node header
pub fn parse_jffs2_node_header(node_data: &[u8]) -> Result<JFFS2Node, StructureError> {
    // Expected JFFS2 node magic
    const JFFS2_CORRECT_MAGIC: usize = 0x1985;

    // Number of header bytes over which the header CRC is calculated
    const JFFS2_HEADER_CRC_SIZE: usize = 8;

    let jffs2_node_structure = vec![
        ("magic", "u16"),
        ("type", "u16"),
        ("size", "u32"),
        ("crc", "u32"),
    ];

    let mut node = JFFS2Node {
        ..Default::default()
    };

    // Try little endian first
    node.endianness = "little".to_string();

    // Parse the node header
    if let Ok(mut node_header) = common::parse(node_data, &jffs2_node_structure, &node.endianness) {
        // If the node header magic isn't correct, try parsing the header as big endian
        if node_header["magic"] != JFFS2_CORRECT_MAGIC {
            node.endianness = "big".to_string();
            match common::parse(node_data, &jffs2_node_structure, &node.endianness) {
                Err(_) => {
                    return Err(StructureError);
                }
                Ok(node_header_be) => {
                    node_header = node_header_be.clone();
                }
            }
        }

        // Node magic must be correct at this point, else this node is invalid
        if node_header["magic"] == JFFS2_CORRECT_MAGIC {
            // Calculate the node header CRC
            let node_calculated_crc = jffs2_node_crc(&node_data[0..JFFS2_HEADER_CRC_SIZE]);

            // Validate the node header CRC
            if node_calculated_crc == node_header["crc"] {
                node.size = node_header["size"];
                node.node_type = node_header["type"] as u16;
                return Ok(node);
            }
        }
    }

    Err(StructureError)
}

/// CRC calculation for JFFS
fn jffs2_node_crc(file_data: &[u8]) -> usize {
    (crc32_v2::crc32(0xFFFFFFFF, file_data) ^ 0xFFFFFFFF) as usize
}
