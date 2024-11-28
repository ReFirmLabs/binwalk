use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store DLink TLV firmware header info
#[derive(Debug, Default, Clone)]
pub struct DlinkTLVHeader {
    pub model_name: String,
    pub board_id: String,
    pub header_size: usize,
    pub data_size: usize,
    pub data_checksum: String,
}

/// Parses a DLink TLV firmware header
pub fn parse_dlink_tlv_header(tlv_data: &[u8]) -> Result<DlinkTLVHeader, StructureError> {
    const MAX_STRING_LENGTH: usize = 0x20;

    const MODEL_NAME_OFFSET: usize = 4;
    const BOARD_ID_OFFSET: usize = 0x24;
    const MD5_HASH_OFFSET: usize = 0x4C;
    const DATA_TLV_OFFSET: usize = 0x6C;

    const HEADER_SIZE: usize = 0x74;
    const EXPECTED_DATA_TYPE: usize = 1;

    let tlv_structure = vec![
        ("type", "u32"),
        ("length", "u32"),
        // value immediately follows
    ];

    let mut header = DlinkTLVHeader {
        ..Default::default()
    };

    // Get the header data
    if let Some(header_data) = tlv_data.get(0..HEADER_SIZE) {
        // Get the strings from the header
        header.board_id =
            get_cstring(&header_data[BOARD_ID_OFFSET..BOARD_ID_OFFSET + MAX_STRING_LENGTH]);
        header.model_name =
            get_cstring(&header_data[MODEL_NAME_OFFSET..MODEL_NAME_OFFSET + MAX_STRING_LENGTH]);
        header.data_checksum =
            get_cstring(&header_data[MD5_HASH_OFFSET..MD5_HASH_OFFSET + MAX_STRING_LENGTH]);

        // Make sure we got the expected strings OK (checksum is not always included)
        if !header.model_name.is_empty() && !header.board_id.is_empty() {
            // Parse the type and length values that describe the data the follows the header
            if let Ok(data_tlv) =
                common::parse(&header_data[DATA_TLV_OFFSET..], &tlv_structure, "little")
            {
                // Sanity check the reported type (should be 1)
                if data_tlv["type"] == EXPECTED_DATA_TYPE {
                    header.data_size = data_tlv["length"];
                    header.header_size = HEADER_SIZE;
                    return Ok(header);
                }
            }
        }
    }

    Err(StructureError)
}
