use crate::structures::common::{self, StructureError};

/// Offset of the APFS magic bytes from the start of the APFS image
pub const MAGIC_OFFSET: usize = 0x20;

/// Struct to store APFS header info
#[derive(Debug, Default, Clone)]
pub struct APFSHeader {
    pub block_size: usize,
    pub block_count: usize,
}

/// Parses an APFS header
pub fn parse_apfs_header(apfs_data: &[u8]) -> Result<APFSHeader, StructureError> {
    const MAX_FS_COUNT: usize = 100;
    const FS_COUNT_BLOCK_SIZE: usize = 512;

    // Partial APFS header, just to figure out the size of the image and validate some fields
    // https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf
    let apfs_structure = vec![
        ("magic", "u32"),
        ("block_size", "u32"),
        ("block_count", "u64"),
        ("nx_features", "u64"),
        ("nx_ro_compat_features", "u64"),
        ("nx_incompat_features", "u64"),
        ("nx_uuid_p1", "u64"),
        ("nx_uuid_p2", "u64"),
        ("nx_next_oid", "u64"),
        ("nx_next_xid", "u64"),
        ("nx_xp_desc_blocks", "u32"),
        ("nx_xp_data_blocks", "u32"),
        ("nx_xp_desc_base", "u64"),
        ("nx_xp_data_base", "u64"),
        ("nx_xp_desc_next", "u32"),
        ("nx_xp_data_next", "u32"),
        ("nx_xp_desc_index", "u32"),
        ("nx_xp_desc_len", "u32"),
        ("nx_xp_data_index", "u32"),
        ("nx_xp_data_len", "u32"),
        ("nx_spaceman_oid", "u64"),
        ("nx_omap_oid", "u64"),
        ("nx_reaper_oid", "u64"),
        ("nx_xp_test_type", "u32"),
        ("nx_xp_max_file_systems", "u32"),
    ];

    // Expected values of superblock flag fields
    let allowed_feature_flags: Vec<usize> = vec![0, 1, 2, 3];
    let allowed_incompat_flags: Vec<usize> = vec![0, 1, 2, 3, 0x100, 0x101, 0x102, 0x103];
    let allowed_ro_compat_flags: Vec<usize> = vec![0];

    let apfs_struct_start = MAGIC_OFFSET;
    let apfs_struct_end = apfs_struct_start + common::size(&apfs_structure);

    // Parse the header
    if let Some(apfs_structure_data) = apfs_data.get(apfs_struct_start..apfs_struct_end) {
        if let Ok(apfs_header) = common::parse(apfs_structure_data, &apfs_structure, "little") {
            // Simple sanity check on the reported block data
            if apfs_header["block_size"] != 0 && apfs_header["block_count"] != 0 {
                // Sanity check the feature flags
                if allowed_feature_flags.contains(&apfs_header["nx_features"])
                    && allowed_ro_compat_flags.contains(&apfs_header["nx_ro_compat_features"])
                    && allowed_incompat_flags.contains(&apfs_header["nx_incompat_features"])
                {
                    // The test_type field *must* be NULL
                    if apfs_header["nx_xp_test_type"] == 0 {
                        // Calculate the file system count; this is max_file_systems divided by 512, rounded up to nearest whole
                        let fs_count = ((apfs_header["nx_xp_max_file_systems"] as f32)
                            / (FS_COUNT_BLOCK_SIZE as f32))
                            .ceil() as usize;

                        // Sanity check the file system count
                        if fs_count > 0 && fs_count <= MAX_FS_COUNT {
                            return Ok(APFSHeader {
                                block_size: apfs_header["block_size"],
                                block_count: apfs_header["block_count"],
                            });
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
