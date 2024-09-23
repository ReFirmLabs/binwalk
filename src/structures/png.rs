use crate::structures;

pub struct PNGChunkHeader {
    pub total_size: usize,
    pub is_last_chunk: bool,
}

pub fn parse_png_chunk_header(
    chunk_data: &[u8],
) -> Result<PNGChunkHeader, structures::common::StructureError> {
    // All PNG chunks are followed by a 4-byte CRC
    const CRC_SIZE: usize = 4;

    // The "IEND" chunk is the last chunk in the PNG
    const IEND_CHUNK_TYPE: usize = 0x49454E44;

    let png_chunk_structure = vec![("length", "u32"), ("type", "u32")];

    let chunk_structure_size: usize = structures::common::size(&png_chunk_structure);

    // Sanity check the size of available data
    if chunk_data.len() > chunk_structure_size {
        // Parse the chunk header
        let chunk_header = structures::common::parse(&chunk_data, &png_chunk_structure, "big");

        return Ok(PNGChunkHeader {
            is_last_chunk: chunk_header["type"] == IEND_CHUNK_TYPE,
            total_size: chunk_structure_size + chunk_header["length"] + CRC_SIZE,
        });
    }

    return Err(structures::common::StructureError);
}
