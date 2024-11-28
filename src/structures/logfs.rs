use crate::structures::common::{self, StructureError};

/// Offset of the LogFS magic bytes from the start of the file system
pub const LOGFS_MAGIC_OFFSET: usize = 0x18;

/// Struct to store LogFS info
#[derive(Debug, Default, Clone)]
pub struct LogFSSuperBlock {
    pub total_size: usize,
}

/// Parses a LogFS superblock
pub fn parse_logfs_super_block(logfs_data: &[u8]) -> Result<LogFSSuperBlock, StructureError> {
    //const LOGFS_CRC_START: usize = LOGFS_MAGIC_OFFSET + 12;
    //const LOGFS_CRC_END: usize = 256;

    let logfs_sb_structure = vec![
        ("magic", "u64"),
        ("crc32", "u32"),
        ("ifile_levels", "u8"),
        ("iblock_levels", "u8"),
        ("data_levels", "u8"),
        ("segment_shift", "u8"),
        ("block_shift", "u8"),
        ("write_shift", "u8"),
        ("pad0", "u32"),
        ("pad1", "u16"),
        ("filesystem_size", "u64"),
        ("segment_size", "u32"),
        ("bad_seg_reserved", "u32"),
        ("feature_incompat", "u64"),
        ("feature_ro_compat", "u64"),
        ("feature_compat", "u64"),
        ("feature_flags", "u64"),
        ("root_reserve", "u64"),
        ("speed_reserve", "u64"),
    ];

    if let Some(sb_struct_data) = logfs_data.get(LOGFS_MAGIC_OFFSET..) {
        if let Ok(super_block) = common::parse(sb_struct_data, &logfs_sb_structure, "big") {
            if super_block["pad0"] == 0 && super_block["pad1"] == 0 {
                return Ok(LogFSSuperBlock {
                    total_size: super_block["filesystem_size"],
                });
            }
        }
    }

    Err(StructureError)
}
