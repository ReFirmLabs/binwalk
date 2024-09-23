use crate::structures;
use std::collections::HashMap;

#[derive(Debug, Default, Clone)]
pub struct SquashFSHeader {
    pub timestamp: usize,
    pub block_size: usize,
    pub image_size: usize,
    pub header_size: usize,
    pub inode_count: usize,
    pub endianness: String,
    pub compression: usize,
    pub major_version: usize,
    pub minor_version: usize,
    pub uid_table_start: usize,
}

pub fn parse_squashfs_header(
    sqsh_data: &[u8],
) -> Result<SquashFSHeader, structures::common::StructureError> {
    const MAX_SQUASHFS_VERSION: u16 = 4;
    const SQUASHFS_VERSION_END: usize = 30;
    const SQUASHFS_VERSION_START: usize = 28;
    const MIN_SQUASHFS_HEADER_SIZE: usize = 120;

    let squashfs_v4_structure = vec![
        ("magic", "u32"),
        ("inode_count", "u32"),
        ("modification_time", "u32"),
        ("block_size", "u32"),
        ("fragment_count", "u32"),
        ("compression_id", "u16"),
        ("block_log", "u16"),
        ("flags", "u16"),
        ("id_count", "u16"),
        ("major_version", "u16"),
        ("minor_version", "u16"),
        ("root_inode_ref", "u64"),
        ("image_size", "u64"),
        ("uid_start", "u64"),
    ];

    let squashfs_v3_structure = vec![
        ("magic", "u32"),
        ("inode_count", "u32"),
        ("bytes_used_2", "u32"),
        ("uid_start_2", "u32"),
        ("guid_start_2", "u32"),
        ("inode_table_start_2", "u32"),
        ("directory_table_start_2", "u32"),
        ("major_version", "u16"),
        ("minor_version", "u16"),
        ("block_size_1", "u16"),
        ("block_log", "u16"),
        ("flags", "u8"),
        ("uid_count", "u8"),
        ("guid_count", "u8"),
        ("modification_time", "u32"),
        ("root_inode_ref", "u64"),
        ("block_size", "u32"),
        ("fragment_entry_count", "u32"),
        ("fragment_table_start_2", "u32"),
        ("image_size", "u64"),
        ("uid_start", "u64"),
        ("guid_start", "u64"),
        ("inode_table_start", "u64"),
        ("directory_table_start", "u64"),
        ("fragment_table_start", "u64"),
        ("lookup_table_start", "u64"),
    ];

    // Default to little endian
    let mut sqsh_header = SquashFSHeader {
        endianness: "little".to_string(),
        ..Default::default()
    };

    // Make sure there is at least enough data to read in a SquashFS header
    if sqsh_data.len() > MIN_SQUASHFS_HEADER_SIZE {
        /*
         * Regardless of the SquashFS version, the version number is always at the same location in the SquashFS suprblock header.
         * This can then be reliably used to determine both the SquashFS superblock header version, as well as the endianess used.
         * Interpret the squashfs major version, assuming little endian.
         */
        let mut squashfs_version: u16 = u16::from_le_bytes(
            sqsh_data[SQUASHFS_VERSION_START..SQUASHFS_VERSION_END]
                .try_into()
                .unwrap(),
        );

        // If the version number doesn't look sane, switch to big endian
        if squashfs_version == 0 || squashfs_version > MAX_SQUASHFS_VERSION {
            sqsh_header.endianness = "big".to_string();
            squashfs_version = u16::from_be_bytes(
                sqsh_data[SQUASHFS_VERSION_START..SQUASHFS_VERSION_END]
                    .try_into()
                    .unwrap(),
            );
        }

        // Sanity check the version number
        if squashfs_version <= MAX_SQUASHFS_VERSION && squashfs_version > 0 {
            let squashfs_header_size: usize;
            let squashfs_header: HashMap<String, usize>;

            // Parse the SquashFS header, using the appropriate version header.
            if squashfs_version == 4 {
                squashfs_header_size = structures::common::size(&squashfs_v4_structure);
                squashfs_header = structures::common::parse(
                    &sqsh_data,
                    &squashfs_v4_structure,
                    &sqsh_header.endianness,
                );
            } else {
                squashfs_header_size = structures::common::size(&squashfs_v3_structure);
                squashfs_header = structures::common::parse(
                    &sqsh_data,
                    &squashfs_v3_structure,
                    &sqsh_header.endianness,
                );
            }

            // Report the total size of this SquashFS image
            sqsh_header.image_size = squashfs_header["image_size"];

            // Make sure the reported image size is at least bigger than the SquashFS header
            if sqsh_header.image_size > MIN_SQUASHFS_HEADER_SIZE {
                // Make sure the block size and block log fields agree
                if squashfs_header["block_size"] > 0
                    && squashfs_header["block_log"]
                        == (squashfs_header["block_size"].ilog2() as usize)
                {
                    // Report relevant squashfs fields
                    sqsh_header.timestamp = squashfs_header["modification_time"];
                    sqsh_header.block_size = squashfs_header["block_size"];
                    sqsh_header.header_size = squashfs_header_size;
                    sqsh_header.inode_count = squashfs_header["inode_count"];
                    sqsh_header.major_version = squashfs_header["major_version"];
                    sqsh_header.minor_version = squashfs_header["minor_version"];
                    sqsh_header.uid_table_start = squashfs_header["uid_start"];

                    // v3 headers don't have a compression ID
                    if squashfs_header.contains_key("compression_id") {
                        sqsh_header.compression = squashfs_header["compression_id"];
                    }

                    return Ok(sqsh_header);
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}

pub fn parse_squashfs_uid_entry(
    uid_data: &[u8],
    version: usize,
    endianness: &String,
) -> Result<usize, structures::common::StructureError> {
    const SQUASHFS_V3_UID_ENTRY_SIZE: usize = 4;
    const SQUASHFS_V4_UID_ENTRY_SIZE: usize = 8;

    let squashfs_v4_uid_table_structure = vec![("uid_block_ptr", "u64")];

    let squashfs_v3_uid_table_structure = vec![("uid_block_ptr", "u32")];

    let uid_entry_size: usize;
    let uid_table: HashMap<String, usize>;

    if version == 4 {
        uid_entry_size = SQUASHFS_V4_UID_ENTRY_SIZE;
    } else {
        uid_entry_size = SQUASHFS_V3_UID_ENTRY_SIZE;
    }

    if uid_data.len() >= uid_entry_size {
        // Parse one entry from the UID table
        if version == 4 {
            uid_table = structures::common::parse(
                &uid_data[0..uid_entry_size],
                &squashfs_v4_uid_table_structure,
                endianness,
            );
        } else {
            uid_table = structures::common::parse(
                &uid_data[0..uid_entry_size],
                &squashfs_v3_uid_table_structure,
                endianness,
            );
        }

        return Ok(uid_table["uid_block_ptr"]);
    }

    return Err(structures::common::StructureError);
}
