use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store DKBS header info
#[derive(Debug, Default, Clone)]
pub struct DKBSHeader {
    pub data_size: usize,
    pub header_size: usize,
    pub board_id: String,
    pub version: String,
    pub boot_device: String,
}

/// Parses a DKBS header
pub fn parse_dkbs_header(dkbs_data: &[u8]) -> Result<DKBSHeader, StructureError> {
    // Header is a fixed size
    const HEADER_SIZE: usize = 0xA0;

    // Constant offsets for strings and known header fields
    const BOARD_ID_START: usize = 0;
    const BOARD_ID_END: usize = 0x20;
    const VERSION_START: usize = 0x28;
    const VERSION_END: usize = 0x48;
    const BOOT_DEVICE_START: usize = 0x70;
    const BOOT_DEVICE_END: usize = 0x90;
    const DATA_SIZE_START: usize = 0x68;
    const DATA_SIZE_END: usize = DATA_SIZE_START + 4;

    let data_size_field = vec![("size", "u32")];

    let mut header = DKBSHeader {
        header_size: HEADER_SIZE,
        ..Default::default()
    };

    // Available data should be at least big enough for the header to fit
    if dkbs_data.len() >= HEADER_SIZE {
        // Parse the version, board ID, and boot device strings
        header.version = get_cstring(&dkbs_data[VERSION_START..VERSION_END]);
        header.board_id = get_cstring(&dkbs_data[BOARD_ID_START..BOARD_ID_END]);
        header.boot_device = get_cstring(&dkbs_data[BOOT_DEVICE_START..BOOT_DEVICE_END]);

        // Sanity check to make sure the strings were retrieved
        if !header.version.is_empty()
            && !header.board_id.is_empty()
            && !header.boot_device.is_empty()
        {
            // Parse the payload size field
            if let Ok(data_size) = common::parse(
                &dkbs_data[DATA_SIZE_START..DATA_SIZE_END],
                &data_size_field,
                "big",
            ) {
                header.data_size = data_size["size"];
                return Ok(header);
            }
        }
    }

    Err(StructureError)
}
