use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Storage struct for CHK header info
#[derive(Debug, Clone, Default)]
pub struct CHKHeader {
    pub header_size: usize,
    pub kernel_size: usize,
    pub rootfs_size: usize,
    pub board_id: String,
}

/// Parse a CHK firmware header
pub fn parse_chk_header(header_data: &[u8]) -> Result<CHKHeader, StructureError> {
    // Somewhat arbitrarily chosen
    const MAX_EXPECTED_HEADER_SIZE: usize = 100;

    let chk_header_structure = vec![
        ("magic", "u32"),
        ("header_size", "u32"),
        ("unknown", "u64"),
        ("kernel_checksum", "u32"),
        ("rootfs_checksum", "u32"),
        ("rootfs_size", "u32"),
        ("kernel_size", "u32"),
        ("image_checksum", "u32"),
        ("header_checksum", "u32"),
        // Board ID string follows
    ];

    // Size of the fixed-length portion of the header structure
    let struct_size: usize = common::size(&chk_header_structure);

    // Parse the CHK header
    if let Ok(chk_header) = common::parse(header_data, &chk_header_structure, "big") {
        // Validate the reported header size
        if chk_header["header_size"] > struct_size
            && chk_header["header_size"] <= MAX_EXPECTED_HEADER_SIZE
        {
            // Read in the board ID string which immediately follows the fixed size structure and extends to the end of the header
            let board_id_start: usize = struct_size;
            let board_id_end: usize = chk_header["header_size"];

            if let Some(board_id_raw_bytes) = header_data.get(board_id_start..board_id_end) {
                let board_id_string = get_cstring(board_id_raw_bytes);

                // We expect that there must be a valid board ID string
                if !board_id_string.is_empty() {
                    return Ok(CHKHeader {
                        board_id: board_id_string.clone(),
                        header_size: chk_header["header_size"],
                        kernel_size: chk_header["kernel_size"],
                        rootfs_size: chk_header["rootfs_size"],
                    });
                }
            }
        }
    }

    Err(StructureError)
}
