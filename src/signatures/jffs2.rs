use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::jffs2::{parse_jffs2_node_header, JFFS2_NODE_STRUCT_SIZE};
use aho_corasick::AhoCorasick;

/// Human readable description
pub const DESCRIPTION: &str = "JFFS2 filesystem";

/// JFFS2 magic bytes
pub fn jffs2_magic() -> Vec<Vec<u8>> {
    /*
     * Big and little endian patterns to search for.
     * These assume that the first JFFS2 node will be a directory, inode, or clean marker type.
     * Longer signatures are less prone to false positive matches.
     */
    vec![
        b"\x19\x85\xe0\x01".to_vec(),
        b"\x19\x85\xe0\x02".to_vec(),
        b"\x19\x85\x20\x03".to_vec(),
        b"\x85\x19\x01\xe0".to_vec(),
        b"\x85\x19\x02\xe0".to_vec(),
        b"\x85\x19\x03\x20".to_vec(),
    ]
}

/// Parse and validate a JFFS2 image
pub fn jffs2_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Useful contstants
    const MAX_PAGE_SIZE: usize = 0x10000;
    const MIN_VALID_NODE_COUNT: usize = 2;
    const JFFS2_BIG_ENDIAN_MAGIC: &[u8; 2] = b"\x19\x85";
    const JFFS2_LITTLE_ENDIAN_MAGIC: &[u8; 2] = b"\x85\x19";

    let mut result = SignatureResult {
        size: 0,
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse this first JFFS2 node header to ensure correctness
    if let Ok(first_node_header) = parse_jffs2_node_header(&file_data[offset..]) {
        // The known end of JFFS2 data in the raw file data. This will be updated as we find more nodes.
        let mut jffs2_eof: usize = offset + roundup(first_node_header.size);

        // Make sure that jffs2_eof is sane
        if jffs2_eof < file_data.len() {
            // Start searching for subsequent JFFS2 nodes at the end of this node's data
            let grep_offset: usize = jffs2_eof;

            // Keep a count of how many valid nodes were found
            let mut node_count: usize = 1;

            // Determine which node magic bytes to search for based on the first node's endianness
            let mut node_magic = JFFS2_LITTLE_ENDIAN_MAGIC;
            if first_node_header.endianness == "big" {
                node_magic = JFFS2_BIG_ENDIAN_MAGIC;
            }

            // Need to grep for all JFFS2 nodes to figure out how big this file system really is
            let grep = AhoCorasick::new(vec![node_magic]).unwrap();

            // Find all matching JFFS2 node magic bytes
            for magic_match in grep.find_overlapping_iter(&file_data[grep_offset..].to_vec()) {
                // Calculate the start and end of the node header inside the file data
                let header_start: usize = grep_offset + magic_match.start();
                let header_end: usize = header_start + JFFS2_NODE_STRUCT_SIZE;

                // This is a false positive that is inside the node data of a previously validated node
                if header_start < jffs2_eof {
                    continue;
                }

                // If we haven't found a valid header within MAX_PAGE_SIZE bytes, quit
                if (header_start - jffs2_eof) > MAX_PAGE_SIZE {
                    break;
                }

                // Get the node header's raw bytes
                match file_data.get(header_start..header_end) {
                    None => {
                        break;
                    }
                    Some(node_header_data) => {
                        // Parse this node's header
                        if let Ok(this_node_header) = parse_jffs2_node_header(node_header_data) {
                            node_count += 1;
                            jffs2_eof = header_start + roundup(this_node_header.size);
                        }
                    }
                }
            }

            // Make sure we've processed at least a few JFFS2 nodes
            if node_count > MIN_VALID_NODE_COUNT {
                result.size = jffs2_eof - result.offset;
                result.description = format!(
                    "{}, {} endian, nodes: {}, total size: {} bytes",
                    result.description, first_node_header.endianness, node_count, result.size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}

/// JFFS2 nodes are padded to a 4 byte boundary
fn roundup(num: usize) -> usize {
    let base: f64 = 4.0;
    let number: f64 = num as f64;
    let div: f64 = number / base;
    (base * div.ceil()) as usize
}
