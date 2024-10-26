use crate::structures::common::{self, StructureError};

/// Struct to store NTFS info
#[derive(Debug, Default, Clone)]
pub struct NTFSPartition {
    pub sector_size: usize,
    pub sector_count: usize,
}

/// Parses an NTFS partition header
pub fn parse_ntfs_header(ntfs_data: &[u8]) -> Result<NTFSPartition, StructureError> {
    // https://en.wikipedia.org/wiki/NTFS
    let ntfs_structure = vec![
        ("opcodes", "u24"),
        ("magic", "u64"),
        ("bytes_per_sector", "u16"),
        ("sectors_per_cluster", "u8"),
        ("unused1", "u16"),
        ("unused2", "u24"),
        ("unused3", "u16"),
        ("media_type", "u8"),
        ("unused4", "u16"),
        ("sectors_per_track", "u16"),
        ("head_count", "u16"),
        ("hidden_sector_count", "u32"),
        ("unused5", "u32"),
        ("unknown", "u32"),
        ("sector_count", "u64"),
    ];

    // Parse the NTFS partition header
    if let Ok(ntfs_header) = common::parse(ntfs_data, &ntfs_structure, "little") {
        // Sanity check to make sure the unused fields are not used
        if ntfs_header["unused1"] == 0
            && ntfs_header["unused2"] == 0
            && ntfs_header["unused3"] == 0
            && ntfs_header["unused4"] == 0
            && ntfs_header["unused5"] == 0
        {
            return Ok(NTFSPartition {
                sector_count: ntfs_header["sector_count"],
                sector_size: ntfs_header["bytes_per_sector"],
            });
        }
    }

    Err(StructureError)
}
