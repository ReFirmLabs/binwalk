use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Storage struct for Pcap block info
#[derive(Debug, Clone, Default)]
pub struct PcapBlock {
    pub block_type: usize,
    pub block_size: usize,
}

/// Parse a Pcap-ng block
pub fn parse_pcapng_block(
    block_data: &[u8],
    endianness: &str,
) -> Result<PcapBlock, StructureError> {
    // Reserved bit in block type field
    const BLOCK_TYPE_RESERVED_MASK: usize = 0x80000000;

    let block_header_structure = vec![("block_type", "u32"), ("block_size", "u32")];

    let block_footer_structure = vec![("block_size", "u32")];

    let mut result = PcapBlock {
        ..Default::default()
    };

    let footer_size = common::size(&block_footer_structure);

    // Parse the block header
    if let Ok(block_header) = common::parse(block_data, &block_header_structure, endianness) {
        // Populate the block type and size values
        result.block_type = block_header["block_type"];
        result.block_size = block_header["block_size"];

        // Make sure the reserved bit of the block type is not set
        if (result.block_type & BLOCK_TYPE_RESERVED_MASK) == 0 {
            // Calculate the block footer offsets
            let block_footer_start = result.block_size - footer_size;
            let block_footer_end = block_footer_start + footer_size;

            // Validate that the block size in the block footer matches the block size in the block header
            if let Some(block_footer_data) = block_data.get(block_footer_start..block_footer_end) {
                if let Ok(block_footer) =
                    common::parse(block_footer_data, &block_footer_structure, endianness)
                {
                    if block_footer["block_size"] == result.block_size {
                        return Ok(result);
                    }
                }
            }
        }
    }

    Err(StructureError)
}

#[derive(Debug, Default, Clone)]
pub struct PcapSectionBlock {
    pub block_size: usize,
    pub endianness: String,
}

/// Parse a Pcap-ng section block
pub fn parse_pcapng_section_block(block_data: &[u8]) -> Result<PcapSectionBlock, StructureError> {
    // Section header block type (same value, regardless of endianness)
    const SECTION_HEADER_BLOCK_TYPE: usize = 0x0A0D0D0A;

    let section_header_structure = vec![
        ("block_type", "u32"),
        ("block_size", "u32"),
        ("endian_magic", "u32"),
        ("major_version", "u16"),
        ("minor_version", "u16"),
        ("section_length", "u32"),
    ];

    let endian_magics: HashMap<usize, &str> =
        HashMap::from([(0x1A2B3C4D, "little"), (0x4D3C2B1A, "big")]);

    let mut result = PcapSectionBlock {
        ..Default::default()
    };

    // Parse the section header structure; endianess doesn't matter (yet)
    if let Ok(section_header) = common::parse(block_data, &section_header_structure, "little") {
        // Determine the endianness based on the endian magic bytes
        if endian_magics.contains_key(&section_header["endian_magic"]) {
            result.endianness = endian_magics[&section_header["endian_magic"]].to_string();

            // Parse the section header block as a generic block to ensure it is valid
            if let Ok(block_header) = parse_pcapng_block(block_data, &result.endianness) {
                // Make sure the section header block type is the expected value
                if block_header.block_type == SECTION_HEADER_BLOCK_TYPE {
                    result.block_size = block_header.block_size;
                    return Ok(result);
                }
            }
        }
    }

    Err(StructureError)
}
