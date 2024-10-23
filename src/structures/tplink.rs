use crate::structures::common::{self, StructureError};

/// Stores info about a TP-Link firmware header
#[derive(Debug, Default, Clone)]
pub struct TPLinkFirmwareHeader {
    pub header_size: usize,
    pub kernel_load_address: usize,
    pub kernel_entry_point: usize,
}

/// Pase a TP-Link firmware header
pub fn parse_tplink_header(tplink_data: &[u8]) -> Result<TPLinkFirmwareHeader, StructureError> {
    // Offset of data structure, after firmware signature
    const STRUCTURE_OFFSET: usize = 0x40;

    // Total size of the firmware header
    const HEADER_SIZE: usize = 0x200;

    // https://github.com/jtreml/firmware-mod-kit/blob/master/src/tpl-tool/doc/Image_layout
    let tplink_structure = vec![
        ("product_id", "u32"),
        ("product_version", "u32"),
        ("reserved1", "u32"),
        ("image_checksum_p1", "u64"),
        ("image_checksum_p2", "u64"),
        ("reserved2", "u32"),
        ("kernel_checksum_p1", "u64"),
        ("kernel_checksum_p2", "u64"),
        ("reserved3", "u32"),
        ("kernel_load_address", "u32"),
        ("kernel_entry_point", "u32"),
        ("image_length", "u32"),
        ("kernel_offset", "u32"),
        ("kernel_length", "u32"),
        ("rootfs_offset", "u32"),
        ("rootfs_length", "u32"),
        ("bootloader_offset", "u32"),
        ("bootloader_length", "u32"),
        ("fw_version_major", "u16"),
        ("fw_version_minor", "u16"),
        ("fw_version_patch", "u16"),
        ("reserved4", "u32"),
    ];

    let mut result = TPLinkFirmwareHeader {
        header_size: HEADER_SIZE,
        ..Default::default()
    };

    // Sanity check available data
    if tplink_data.len() >= HEADER_SIZE {
        if let Some(structure_data) = tplink_data.get(STRUCTURE_OFFSET..) {
            // Parse the header
            if let Ok(tplink_header) = common::parse(structure_data, &tplink_structure, "little") {
                // Make sure the reserved fields are NULL
                if tplink_header["reserved1"] == 0
                    && tplink_header["reserved2"] == 0
                    && tplink_header["reserved3"] == 0
                    && tplink_header["reserved4"] == 0
                {
                    // Unfortunately, most header fields aren't reliably used; these seem to be, so report them
                    result.kernel_entry_point = tplink_header["kernel_entry_point"];
                    result.kernel_load_address = tplink_header["kernel_load_address"];
                    return Ok(result);
                }
            }
        }
    }

    Err(StructureError)
}

/// Stores info about a TP-Link RTOS firmware header
#[derive(Debug, Default, Clone)]
pub struct TPLinkRTOSFirmwareHeader {
    pub header_size: usize,
    pub total_size: usize,
    pub model_number: usize,
    pub hardware_rev_major: usize,
    pub hardware_rev_minor: usize,
}

/// Parse a TP-Link RTOS firmware header
pub fn parse_tplink_rtos_header(
    tplink_data: &[u8],
) -> Result<TPLinkRTOSFirmwareHeader, StructureError> {
    const HEADER_SIZE: usize = 0x94;
    const MAGIC2_VALUE: usize = 0x494D4730;
    const TOTAL_SIZE_OFFSET: usize = 20;

    let tplink_rtos_structure = vec![
        ("magic1", "u32"),
        ("unknown1", "u64"),
        ("unknown2", "u64"),
        ("magic2", "u32"),
        ("data_size", "u32"),
        ("model_number", "u16"),
        ("hardware_revision_major", "u8"),
        ("hardware_revision_minor", "u8"),
    ];

    if let Ok(header) = common::parse(tplink_data, &tplink_rtos_structure, "big") {
        if header["magic2"] == MAGIC2_VALUE {
            return Ok(TPLinkRTOSFirmwareHeader {
                header_size: HEADER_SIZE,
                total_size: header["data_size"] + TOTAL_SIZE_OFFSET,
                model_number: header["model_number"],
                hardware_rev_major: header["hardware_revision_major"],
                hardware_rev_minor: header["hardware_revision_minor"],
            });
        }
    }

    Err(StructureError)
}
