use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Expected size of an EXT superblock
pub const SUPERBLOCK_SIZE: usize = 1024;

/// Expected file offset of an EXT superblock
pub const SUPERBLOCK_OFFSET: usize = 1024;

/// Struct to store some useful EXT info
#[derive(Debug, Default, Clone)]
pub struct EXTHeader {
    pub os: String,
    pub block_size: usize,
    pub image_size: usize,
    pub blocks_count: usize,
    pub inodes_count: usize,
    pub free_blocks_count: usize,
    pub reserved_blocks_count: usize,
}

/// Partially parses an EXT superblock structure
pub fn parse_ext_header(ext_data: &[u8]) -> Result<EXTHeader, StructureError> {
    // Max value of the EXT log block size
    const MAX_BLOCK_LOG: usize = 2;

    // Parital superblock structure, just enough for validation and size calculation
    let ext_superblock_structure = vec![
        ("inodes_count", "u32"),
        ("blocks_count", "u32"),
        ("reserved_blocks_count", "u32"),
        ("free_blocks_count", "u32"),
        ("free_inodes_count", "u32"),
        ("first_data_block", "u32"),
        ("log_block_size", "u32"),
        ("log_frag_size", "u32"),
        ("blocks_per_group", "u32"),
        ("frags_per_group", "u32"),
        ("inodes_per_group", "u32"),
        ("modification_time", "u32"),
        ("write_time", "u32"),
        ("mount_count", "u16"),
        ("max_mount_count", "u16"),
        ("magic", "u16"),
        ("state", "u16"),
        ("errors", "u16"),
        ("s_minor_rev_level", "u16"),
        ("last_check", "u32"),
        ("check_interval", "u32"),
        ("creator_os", "u32"),
        ("s_rev_level", "u32"),
        ("resuid", "u16"),
        ("resgid", "u16"),
    ];

    let allowed_rev_levels: Vec<usize> = vec![0, 1];
    let allowed_first_data_blocks: Vec<usize> = vec![0, 1];

    let supported_os: HashMap<usize, &str> = HashMap::from([
        (0, "Linux"),
        (1, "GNU HURD"),
        (2, "MASIX"),
        (3, "FreeBSD"),
        (4, "Lites"),
    ]);

    let mut ext_header = EXTHeader {
        ..Default::default()
    };

    // Sanity check the available data
    if ext_data.len() >= (SUPERBLOCK_OFFSET + SUPERBLOCK_SIZE) {
        // Parse the EXT superblock structure
        if let Ok(ext_superblock) = common::parse(
            &ext_data[SUPERBLOCK_OFFSET..],
            &ext_superblock_structure,
            "little",
        ) {
            // Sanity check the reported OS this EXT image was created on
            if supported_os.contains_key(&ext_superblock["creator_os"]) {
                // Sanity check the s_rev_level field
                if allowed_rev_levels.contains(&ext_superblock["s_rev_level"]) {
                    // Sanity check the first_data_block field, which must be either 0 or 1
                    if allowed_first_data_blocks.contains(&ext_superblock["first_data_block"]) {
                        // Santiy check the log_block_size
                        if ext_superblock["log_block_size"] <= MAX_BLOCK_LOG {
                            // Update the reported image info
                            ext_header.blocks_count = ext_superblock["blocks_count"];
                            ext_header.inodes_count = ext_superblock["inodes_count"];
                            ext_header.block_size = 1024 << ext_superblock["log_block_size"];
                            ext_header.free_blocks_count = ext_superblock["free_blocks_count"];
                            ext_header.os = supported_os[&ext_superblock["creator_os"]].to_string();
                            ext_header.reserved_blocks_count =
                                ext_superblock["reserved_blocks_count"];
                            ext_header.image_size =
                                ext_header.block_size * ext_superblock["blocks_count"];

                            return Ok(ext_header);
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
