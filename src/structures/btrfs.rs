use crate::structures::common::{self, StructureError};
use crc32c::crc32c;

/// Struct to store BTRFS super block info
#[derive(Debug, Default, Clone)]
pub struct BTRFSHeader {
    pub bytes_used: usize,
    pub total_size: usize,
    pub leaf_size: usize,
    pub node_size: usize,
    pub stripe_size: usize,
    pub sector_size: usize,
}

/// Parse and validate a BTRFS super block
pub fn parse_btrfs_header(btrfs_data: &[u8]) -> Result<BTRFSHeader, StructureError> {
    const SUPERBLOCK_OFFSET: usize = 0x10000;
    const SUPERBLOCK_END: usize = SUPERBLOCK_OFFSET + 0x1000;
    const CRC_START: usize = 0x20;

    // Partial BTRFS superblock structure for obtaining image size and CRC validation
    // https://archive.kernel.org/oldwiki/btrfs.wiki.kernel.org/index.php/On-disk_Format.html#Superblock
    let btrfs_structure = vec![
        ("header_checksum", "u32"),
        ("unused1", "u32"),
        ("unused2", "u64"),
        ("unused3", "u64"),
        ("unused4", "u64"),
        ("uuid_p1", "u64"),
        ("uuid_p2", "u64"),
        ("block_phys_addr", "u64"),
        ("flags", "u64"),
        ("magic", "u64"),
        ("generation", "u64"),
        ("root_tree_address", "u64"),
        ("chunk_tree_address", "u64"),
        ("log_tree_address", "u64"),
        ("log_root_transid", "u64"),
        ("total_bytes", "u64"),
        ("bytes_used", "u64"),
        ("root_dir_objid", "u64"),
        ("num_devices", "u64"),
        ("sector_size", "u32"),
        ("node_size", "u32"),
        ("leaf_size", "u32"),
        ("stripe_size", "u32"),
    ];

    // Parse the header
    if let Some(btrfs_header_data) = btrfs_data.get(SUPERBLOCK_OFFSET..SUPERBLOCK_END) {
        if let Ok(btrfs_header) = common::parse(btrfs_header_data, &btrfs_structure, "little") {
            // Validate the superblock CRC
            if btrfs_header["header_checksum"] == (crc32c(&btrfs_header_data[CRC_START..]) as usize)
            {
                return Ok(BTRFSHeader {
                    sector_size: btrfs_header["sector_size"],
                    node_size: btrfs_header["node_size"],
                    leaf_size: btrfs_header["leaf_size"],
                    stripe_size: btrfs_header["stripe_size"],
                    bytes_used: btrfs_header["bytes_used"],
                    total_size: btrfs_header["total_bytes"],
                });
            }
        }
    }

    Err(StructureError)
}
