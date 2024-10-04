use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Struct to store JBOOT ARM firmware image info
#[derive(Debug, Default, Clone)]
pub struct JBOOTArmHeader {
    pub header_size: usize,
    pub data_size: usize,
    pub data_offset: usize,
    pub erase_offset: usize,
    pub erase_size: usize,
    pub rom_id: String,
}

/// Parses a JBOOT ARM image header
pub fn parse_jboot_arm_header(jboot_data: &[u8]) -> Result<JBOOTArmHeader, StructureError> {
    // Structure starts after 12-byte ROM ID
    const STRUCTURE_OFFSET: usize = 12;

    // Some expected header values
    const LPVS_VALUE: usize = 1;
    const MBZ_VALUE: usize = 0;
    const HEADER_ID_VALUE: usize = 0x4842;
    const HEADER_VERSION_VALUE: usize = 2;

    let arm_structure = vec![
        ("drange", "u16"),
        ("image_checksum", "u16"),
        ("reserved1", "u32"),
        ("reserved2", "u32"),
        ("reserved3", "u16"),
        ("lpvs", "u8"),
        ("mbz", "u8"),
        ("timestamp", "u32"),
        ("erase_start", "u32"),
        ("erase_size", "u32"),
        ("data_start", "u32"),
        ("data_size", "u32"),
        ("reserved4", "u32"),
        ("reserved5", "u32"),
        ("reserved6", "u32"),
        ("reserved7", "u32"),
        ("header_id", "u16"),
        ("header_version", "u16"),
        ("reserved8", "u16"),
        ("section_id", "u8"),
        ("image_info_type", "u8"),
        ("image_info_offset", "u32"),
        ("family", "u16"),
        ("header_checksum", "u16"),
    ];

    if let Some(header_data) = jboot_data.get(STRUCTURE_OFFSET..) {
        // Parse the header structure
        if let Ok(arm_header) = common::parse(header_data, &arm_structure, "little") {
            // Make sure the reserved fields are NULL
            if arm_header["reserved1"] == 0
                && arm_header["reserved2"] == 0
                && arm_header["reserved3"] == 0
                && arm_header["reserved4"] == 0
                && arm_header["reserved5"] == 0
                && arm_header["reserved6"] == 0
                && arm_header["reserved7"] == 0
                && arm_header["reserved8"] == 0
            {
                // Sanity check expected header values
                if arm_header["lpvs"] == LPVS_VALUE
                    && arm_header["mbz"] == MBZ_VALUE
                    && arm_header["header_id"] == HEADER_ID_VALUE
                    && arm_header["header_version"] == HEADER_VERSION_VALUE
                {
                    // TODO: Validate header checksum
                    return Ok(JBOOTArmHeader {
                        header_size: STRUCTURE_OFFSET + common::size(&arm_structure),
                        rom_id: get_cstring(&jboot_data[0..STRUCTURE_OFFSET]),
                        data_size: arm_header["data_size"],
                        data_offset: arm_header["data_start"],
                        erase_offset: arm_header["erase_start"],
                        erase_size: arm_header["erase_size"],
                    });
                }
            }
        }
    }

    return Err(StructureError);
}

/// Stores info about JBOOT STAG headers
#[derive(Debug, Default, Clone)]
pub struct JBOOTStagHeader {
    pub header_size: usize,
    pub image_size: usize,
    pub is_factory_image: bool,
    pub is_sysupgrade_image: bool,
}

/// Parses a JBOOT STAG header
pub fn parse_jboot_stag_header(jboot_data: &[u8]) -> Result<JBOOTStagHeader, StructureError> {
    // cmark value for factory images; for system upgrade images, cmark must equal id
    const FACTORY_IMAGE_TYPE: usize = 0xFF;

    let stag_structure = vec![
        ("cmark", "u8"),
        ("id", "u8"),
        ("magic", "u16"),
        ("timestamp", "u32"),
        ("image_size", "u32"),
        ("image_checksum", "u16"),
        ("header_checksum", "u16"),
    ];

    let mut result = JBOOTStagHeader {
        ..Default::default()
    };

    // Parse the header structure
    if let Ok(stag_header) = common::parse(jboot_data, &stag_structure, "little") {
        result.header_size = common::size(&stag_structure);
        result.image_size = stag_header["image_size"];
        result.is_factory_image = stag_header["cmark"] == FACTORY_IMAGE_TYPE;
        result.is_sysupgrade_image = stag_header["cmark"] == stag_header["id"];

        // TODO: Validate checksums
        if result.is_factory_image || result.is_sysupgrade_image {
            return Ok(result);
        }
    }

    return Err(StructureError);
}

#[derive(Default, Debug, Clone)]
pub struct JBOOTSchHeader {
    pub header_size: usize,
    pub compression: String,
    pub kernel_size: usize,
    pub kernel_entry_point: usize,
    pub rootfs_address: usize,
    pub rootfs_size: usize,
}

/// Parses a JBOOT SCH2 header
pub fn parse_jboot_sch2_header(jboot_data: &[u8]) -> Result<JBOOTSchHeader, StructureError> {
    const VERSION_VALUE: usize = 2;

    let sch2_structure = vec![
        ("magic", "u16"),
        ("compression_type", "u8"),
        ("version", "u8"),
        ("ram_entry_address", "u32"),
        ("kernel_image_size", "u32"),
        ("kernel_image_crc", "u32"),
        ("ram_start_address", "u32"),
        ("rootfs_flash_address", "u32"),
        ("rootfs_size", "u32"),
        ("rootfs_crc", "u32"),
        ("header_crc", "u32"),
        ("header_size", "u16"),
        ("cmd_line_size", "u16"),
    ];

    let compression_types: HashMap<usize, &str> =
        HashMap::from([(0, "none"), (1, "jz"), (2, "gzip"), (3, "lzma")]);

    let mut result = JBOOTSchHeader {
        header_size: common::size(&sch2_structure),
        ..Default::default()
    };

    if let Ok(sch2_header) = common::parse(jboot_data, &sch2_structure, "little") {
        if sch2_header["version"] == VERSION_VALUE {
            if sch2_header["header_size"] == result.header_size {
                if compression_types.contains_key(&sch2_header["compression_type"]) {
                    // TODO: Validate checksums
                    result.compression =
                        compression_types[&sch2_header["compression_type"]].to_string();
                    result.kernel_size = sch2_header["kernel_image_size"];
                    result.kernel_entry_point = sch2_header["ram_entry_address"];
                    result.rootfs_address = sch2_header["rootfs_flash_address"];
                    result.rootfs_size = sch2_header["rootfs_size"];
                    return Ok(result);
                }
            }
        }
    }

    return Err(StructureError);
}
