use crate::common::crc32;
use crate::structures::common::{self, StructureError};

/// Stores UBI superblock header info
#[derive(Debug, Default, Clone)]
pub struct UbiSuperBlockHeader {
    pub leb_size: usize,
    pub leb_count: usize,
}

/// Partially parse a UBI superblock header
pub fn parse_ubi_superblock_header(ubi_data: &[u8]) -> Result<UbiSuperBlockHeader, StructureError> {
    // Type & offset constants
    const MAX_GROUP_TYPE: usize = 2;
    const CRC_START_OFFSET: usize = 8;
    const SUPERBLOCK_NODE_TYPE: usize = 6;

    // There are some other fields in the superblock header that we don't parse because we don't really care about them...
    const SUPERBLOCK_STRUCTURE_EXTRA_SIZE: usize = 3968;

    let ubi_sb_structure = vec![
        ("magic", "u32"),
        ("header_crc", "u32"),
        ("sequence_number", "u64"),
        ("node_len", "u32"),
        ("node_type", "u8"),
        ("group_type", "u8"),
        ("padding1", "u32"),
        ("key_hash", "u8"),
        ("key_format", "u8"),
        ("flags", "u32"),
        ("min_io_size", "u32"),
        ("leb_size", "u32"),
        ("leb_count", "u32"),
        ("max_leb_count", "u32"),
        ("max_bud_bytes", "u64"),
        ("log_lebs", "u32"),
        ("lpt_lebs", "u32"),
        ("orph_lebs", "u32"),
        ("jhead_count", "u32"),
        ("fanout", "u32"),
        ("lsave_count", "u32"),
        ("fmt_version", "u32"),
        ("default_compression", "u16"),
        ("padding2", "u16"),
        ("rp_uid", "u32"),
        ("rp_gid", "u32"),
        ("rp_size", "u64"),
        ("time_gran", "u32"),
        ("uuid_p1", "u64"),
        ("uuid_p2", "u64"),
        ("ro_compat_version", "u32"),
    ];

    let sb_struct_size: usize = common::size(&ubi_sb_structure) + SUPERBLOCK_STRUCTURE_EXTRA_SIZE;

    // Parse the UBI superblock header
    if let Ok(sb_header) = common::parse(ubi_data, &ubi_sb_structure, "little") {
        // Make sure the padding fields are NULL
        if sb_header["padding1"] == 0 && sb_header["padding2"] == 0 {
            // Make sure the node type is SUPERBLOCK
            if sb_header["node_type"] == SUPERBLOCK_NODE_TYPE {
                // Make sure the group type is valid
                if sb_header["group_type"] <= MAX_GROUP_TYPE {
                    // Validate the header CRC, which is calculated over the entire header except for the magic bytes and CRC field
                    if let Some(crc_data) = ubi_data.get(CRC_START_OFFSET..sb_struct_size) {
                        if ubi_crc(crc_data) == sb_header["header_crc"] {
                            return Ok(UbiSuperBlockHeader {
                                leb_size: sb_header["leb_size"],
                                leb_count: sb_header["leb_count"],
                            });
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}

/// Stores info about a UBI erase count header
#[derive(Debug, Default, Clone)]
pub struct UbiECHeader {
    pub version: usize,
    pub data_offset: usize,
    pub volume_id_offset: usize,
}

/// Parse a UBI erase count header
pub fn parse_ubi_ec_header(ubi_data: &[u8]) -> Result<UbiECHeader, StructureError> {
    let ubi_ec_structure = vec![
        ("magic", "u32"),
        ("version", "u8"),
        ("padding1", "u24"),
        ("ec", "u64"),
        ("volume_id_header_offset", "u32"),
        ("data_offset", "u32"),
        ("image_sequence_number", "u32"),
        ("padding2", "u64"),
        ("padding3", "u64"),
        ("padding4", "u64"),
        ("padding5", "u64"),
        ("header_crc", "u32"),
    ];

    let ec_header_size: usize = common::size(&ubi_ec_structure);
    let crc_data_size: usize = ec_header_size - std::mem::size_of::<u32>();

    // Parse the first half of the header
    if let Ok(ubi_ec_header) = common::parse(ubi_data, &ubi_ec_structure, "big") {
        // Padding fields must be NULL
        if ubi_ec_header["padding1"] == 0
            && ubi_ec_header["padding2"] == 0
            && ubi_ec_header["padding3"] == 0
            && ubi_ec_header["padding4"] == 0
            && ubi_ec_header["padding5"] == 0
        {
            // Offsets should be beyond the EC header
            if ubi_ec_header["data_offset"] >= ec_header_size
                && ubi_ec_header["volume_id_header_offset"] >= ec_header_size
            {
                // Validate the header CRC
                if let Some(crc_data) = ubi_data.get(0..crc_data_size) {
                    if ubi_crc(crc_data) == ubi_ec_header["header_crc"] {
                        return Ok(UbiECHeader {
                            version: ubi_ec_header["version"],
                            data_offset: ubi_ec_header["data_offset"],
                            volume_id_offset: ubi_ec_header["volume_id_header_offset"],
                        });
                    }
                }
            }
        }
    }

    Err(StructureError)
}

/// Dummy structure indicating a UBI volume header was parsed successfully
#[derive(Debug, Default, Clone)]
pub struct UbiVolumeHeader;

/// Parse a UBI volume header
pub fn parse_ubi_volume_header(ubi_data: &[u8]) -> Result<UbiVolumeHeader, StructureError> {
    let ubi_vol_structure = vec![
        ("magic", "u32"),
        ("version", "u8"),
        ("volume_type", "u8"),
        ("copy_flag", "u8"),
        ("compat_type", "u8"),
        ("volume_id", "u32"),
        ("logical_erase_block_number", "u32"),
        ("padding1", "u32"),
        ("data_size", "u32"),
        ("used_erase_block_count", "u32"),
        ("data_padding_size", "u32"),
        ("data_crc", "u32"),
        ("padding2", "u32"),
        ("sequence_number", "u64"),
        ("padding3", "u64"),
        ("padding4", "u32"),
        ("header_crc", "u32"),
    ];

    let vol_header_size: usize = common::size(&ubi_vol_structure);
    let crc_data_size: usize = vol_header_size - std::mem::size_of::<u32>();

    // Parse the volume header
    if let Ok(ubi_vol_header) = common::parse(ubi_data, &ubi_vol_structure, "big") {
        // Sanity check padding fields, they should all be null
        if ubi_vol_header["padding1"] == 0
            && ubi_vol_header["padding2"] == 0
            && ubi_vol_header["padding3"] == 0
            && ubi_vol_header["padding4"] == 0
        {
            // Validate the header CRC
            if let Some(crc_data) = ubi_data.get(0..crc_data_size) {
                if ubi_crc(crc_data) == ubi_vol_header["header_crc"] {
                    return Ok(UbiVolumeHeader);
                }
            }
        }
    }

    Err(StructureError)
}

/// Calculate a UBI checksum
fn ubi_crc(data: &[u8]) -> usize {
    const UBI_CRC_INIT: u32 = 0xFFFFFFFF;
    ((!crc32(data)) & UBI_CRC_INIT) as usize
}
