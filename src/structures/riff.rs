use crate::structures::common::{self, StructureError};

/// Struct to store info from a RIFF header
pub struct RIFFHeader {
    pub size: usize,
    pub chunk_type: String,
}

/// Parse a RIFF image header
pub fn parse_riff_header(riff_data: &[u8]) -> Result<RIFFHeader, StructureError> {
    const MAGIC: usize = 0x46464952;

    const CHUNK_TYPE_START: usize = 8;
    const CHUNK_TYPE_END: usize = 12;

    const FILE_SIZE_OFFSET: usize = 8;

    let riff_structure = vec![
        ("magic", "u32"),
        ("file_size", "u32"),
        ("chunk_type", "u32"),
    ];

    // Parse the riff header
    if let Ok(riff_header) = common::parse(riff_data, &riff_structure, "little") {
        // Sanity check expected magic bytes
        if riff_header["magic"] == MAGIC {
            // Get the RIFF type string (e.g., "WAVE")
            if let Ok(type_string) =
                String::from_utf8(riff_data[CHUNK_TYPE_START..CHUNK_TYPE_END].to_vec())
            {
                return Ok(RIFFHeader {
                    size: riff_header["file_size"] + FILE_SIZE_OFFSET,
                    chunk_type: type_string.trim().to_string(),
                });
            }
        }
    }

    Err(StructureError)
}
