use crate::structures::common::{self, StructureError};

/// Stores info on a PNG chunk header
pub struct PNGChunkHeader {
    pub total_size: usize,
    pub is_last_chunk: bool,
}

/// Parse a PNG chunk header
pub fn parse_png_chunk_header(chunk_data: &[u8]) -> Result<PNGChunkHeader, StructureError> {
    // All PNG chunks are followed by a 4-byte CRC
    const CRC_SIZE: usize = 4;

    // The "IEND" chunk is the last chunk in the PNG
    const IEND_CHUNK_TYPE: usize = 0x49454E44;

    let png_chunk_structure = vec![("length", "u32"), ("type", "u32")];

    let chunk_structure_size: usize = common::size(&png_chunk_structure);

    // Parse the chunk header
    if let Ok(chunk_header) = common::parse(chunk_data, &png_chunk_structure, "big") {
        return Ok(PNGChunkHeader {
            is_last_chunk: chunk_header["type"] == IEND_CHUNK_TYPE,
            total_size: chunk_structure_size + chunk_header["length"] + CRC_SIZE,
        });
    }

    Err(StructureError)
}
