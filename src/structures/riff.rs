use crate::structures::common::{self, StructureError};

/// Struct to store info from a RIFF header
pub struct RIFFHeader {
    pub size: usize,
    pub chunk_type: String,
}

/// Parse a RIFF image header
pub fn parse_riff_header(riff_data: &[u8]) -> Result<RIFFHeader, StructureError> {
    const MAGIC1: usize = 0x46464952;
    const MAGIC2: usize = 0x50424557;

    const CHUNK_TYPE_START: usize = 12;
    const CHUNK_TYPE_END: usize = 15;

    const FILE_SIZE_OFFSET: usize = 8;

    let riff_structure = vec![
        ("magic1", "u32"),
        ("file_size", "u32"),
        ("magic2", "u32"),
        ("chunk_type", "u32"),
    ];

    // Parse the riff header
    if let Ok(riff_header) = common::parse(riff_data, &riff_structure, "little") {
        // Sanity check expected magic bytes
        if riff_header["magic1"] == MAGIC1 && riff_header["magic2"] == MAGIC2 {
            // Get the RIFF type string (e.g., "WAV")
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
