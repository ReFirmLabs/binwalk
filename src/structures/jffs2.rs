use crc32_v2;
use crate::structures;

pub const JFFS2_NODE_STRUCT_SIZE: usize = 12;

#[derive(Debug, Default, Clone)]
pub struct JFFS2Node {
    pub size: usize,
    pub node_type: u16,
    pub endianness: String,
}

pub fn parse_jffs2_node_header(node_data: &[u8]) -> Result<JFFS2Node, structures::common::StructureError> {

    const JFFS2_CORRECT_MAGIC: usize = 0x1985;
    const JFFS2_HEADER_CRC_SIZE: usize = 8;

    let jffs2_node_structure = vec![
        ("magic", "u16"),
        ("type", "u16"),
        ("size", "u32"),
        ("crc", "u32"),
    ];

    let mut node = JFFS2Node { ..Default::default() };
    let node_header_size = JFFS2_NODE_STRUCT_SIZE;

    // Try little endian first
    node.endianness = "little".to_string();

    // Sanity check size of available data
    if node_data.len() >= node_header_size {
        // Parse the node header
        let mut node_header = structures::common::parse(&node_data[0..node_header_size], &jffs2_node_structure, &node.endianness);

        // If the node header magic isn't correct, try parsing the header as big endian
        if node_header["magic"] != JFFS2_CORRECT_MAGIC {
            node.endianness = "big".to_string();
            node_header = structures::common::parse(&node_data[0..node_header_size], &jffs2_node_structure, &node.endianness);
        }

        // Node magic must be correct at this point, else this node is invalid
        if node_header["magic"] == JFFS2_CORRECT_MAGIC {

            // Calculate the node header CRC
            let first_node_calculated_crc = jffs2_node_crc(&node_data[0..JFFS2_HEADER_CRC_SIZE]);

            // Validate the node header CRC
            if first_node_calculated_crc == node_header["crc"] {
                node.size = node_header["size"];
                node.node_type = node_header["type"] as u16;
                return Ok(node);
            }
        }
    }

    return Err(structures::common::StructureError);
}

fn jffs2_node_crc(file_data: &[u8]) -> usize {
    return (crc32_v2::crc32(0xFFFFFFFF, &file_data) ^ 0xFFFFFFFF) as usize;
}
