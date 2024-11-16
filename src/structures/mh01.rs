use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store MH01 header info
#[derive(Debug, Default, Clone)]
pub struct MH01Header {
    pub iv: String,
    pub iv_offset: usize,
    pub iv_size: usize,
    pub signature_offset: usize,
    pub signature_size: usize,
    pub encrypted_data_offset: usize,
    pub encrypted_data_size: usize,
    pub total_size: usize,
}

/// Parses an MH01 header
pub fn parse_mh01_header(mh01_data: &[u8]) -> Result<MH01Header, StructureError> {
    const HEADER_SIZE: usize = 16;

    // This structure is actually two MH01 headers, each header is HEADER_SIZE bytes long.
    // The first header describes the offset and size of the firmware signature.
    // The second header describes the offset and size of the encrypted firmware image.
    // The OpenSSL IV is stored as an ASCII hex string between the second header and the encrypted firmware image.
    let mh01_structure = vec![
        ("magic1", "u32"),
        ("signature_offset", "u32"),
        ("signature_size", "u32"),
        ("unknown1", "u32"),
        ("magic2", "u32"),
        ("iv_size", "u32"),
        ("encrypted_data_size", "u32"),
        ("unknown2", "u32"),
        // IV string of length iv_size immediately follows
    ];

    let mut result = MH01Header {
        ..Default::default()
    };

    // Parse the header
    if let Ok(header) = common::parse(mh01_data, &mh01_structure, "little") {
        // Make sure the expected magic bytes match
        if header["magic1"] == header["magic2"] {
            // IV size is specified in the header and immediately follows the header
            result.iv_size = header["iv_size"];
            result.iv_offset = common::size(&mh01_structure);

            // The encrypted firmware image immediately follows the IV
            result.encrypted_data_size = header["encrypted_data_size"];
            result.encrypted_data_offset = result.iv_offset + result.iv_size;

            // The signature should immediately follow the encrypted firmware image
            result.signature_size = header["signature_size"];
            result.signature_offset = HEADER_SIZE + header["signature_offset"];

            // Calculate the start and end bytes of the IV (ASCII hex)
            let iv_bytes_start = result.iv_offset;
            let iv_bytes_end = result.encrypted_data_offset;

            // Get the payload hash string
            if let Some(iv_bytes) = mh01_data.get(iv_bytes_start..iv_bytes_end) {
                let iv_string = get_cstring(iv_bytes);

                // Make sure we got a string of the expected length
                if iv_string.len() == result.iv_size {
                    result.iv = iv_string.trim().to_string();
                    result.total_size = result.signature_offset + result.signature_size;
                    return Ok(result);
                }
            }
        }
    }

    Err(StructureError)
}
