use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Struct to store MH01 header info
#[derive(Debug, Default, Clone)]
pub struct MH01Header {
    pub data_size: usize,
    pub header_size: usize,
    pub data_hash: String,
}

/// Parses an MH01 header
pub fn parse_mh01_header(mh01_data: &[u8]) -> Result<MH01Header, StructureError> {
    let mh01_structure = vec![
        ("magic1", "u32"),
        ("image_size", "u32"),
        ("footer_size", "u32"),
        ("unknown1", "u32"),
        ("magic2", "u32"),
        ("hash_size", "u32"),
        ("encrypted_data_size", "u32"),
        ("unknown2", "u32"),
        // hash string of length hash_size immediately follows
    ];

    // Parse the header
    if let Ok(header) = common::parse(mh01_data, &mh01_structure, "little") {
        // Make sure the expected magic bytes match
        if header["magic1"] == header["magic2"] {
            // Calculate the start and end bytes of the payload hash (ASCII hex)
            let hash_bytes_start = common::size(&mh01_structure);
            let hash_bytes_end = hash_bytes_start + header["hash_size"];

            // Get the payload hash string
            if let Some(hash_bytes) = mh01_data.get(hash_bytes_start..hash_bytes_end) {
                let hash_string = get_cstring(hash_bytes);

                // Make sure we got a string of the expected length
                if hash_string.len() == header["hash_size"] {
                    return Ok(MH01Header {
                        data_size: header["encrypted_data_size"],
                        header_size: hash_bytes_end,
                        data_hash: hash_string.trim().to_string(),
                    });
                }
            }
        }
    }

    Err(StructureError)
}
