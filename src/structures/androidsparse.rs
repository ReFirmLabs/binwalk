use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct AndroidSparseHeader {
    pub major_version: usize,
    pub minor_version: usize,
    pub header_size: usize,
    pub block_size: usize,
    pub chunk_count: usize,
}

pub fn parse_android_sparse_header(
    sparse_data: &[u8],
) -> Result<AndroidSparseHeader, structures::common::StructureError> {
    // Version must be 1.0
    const MAJOR_VERSION: usize = 1;
    const MINOR_VERSION: usize = 0;

    // Blocks must be aligned on a 4-byte boundary
    const BLOCK_ALIGNMENT: usize = 4;

    // Expected value for the reported chunk header size
    const CHUNK_HEADER_SIZE: usize = 12;

    let android_sparse_structure = vec![
        ("magic", "u32"),
        ("major_version", "u16"),
        ("minor_version", "u16"),
        ("header_size", "u16"),
        ("chunk_header_size", "u16"),
        ("block_size", "u32"),
        ("block_count", "u32"),
        ("total_chunks", "u32"),
        ("checksum", "u32"),
    ];

    let header_size = structures::common::size(&android_sparse_structure);

    // Sanity check the size of available data
    if sparse_data.len() > header_size {
        // Parse the header
        let header = structures::common::parse(&sparse_data, &android_sparse_structure, "little");

        // Sanity check header values
        if header["major_version"] == MAJOR_VERSION
            && header["minor_version"] == MINOR_VERSION
            && header["header_size"] == header_size
            && header["chunk_header_size"] == CHUNK_HEADER_SIZE
            && (header["block_size"] % BLOCK_ALIGNMENT) == 0
        {
            return Ok(AndroidSparseHeader {
                major_version: header["major_version"],
                minor_version: header["minor_version"],
                header_size: header["header_size"],
                block_size: header["block_size"],
                chunk_count: header["total_chunks"],
            });
        }
    }

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct AndroidSparseChunkHeader {
    pub header_size: usize,
    pub data_size: usize,
    pub block_count: usize,
    pub is_crc: bool,
    pub is_raw: bool,
    pub is_fill: bool,
    pub is_dont_care: bool,
}

pub fn parse_android_sparse_chunk_header(
    chunk_data: &[u8],
) -> Result<AndroidSparseChunkHeader, structures::common::StructureError> {
    // Known chunk types
    const CHUNK_TYPE_RAW: usize = 0xCAC1;
    const CHUNK_TYPE_FILL: usize = 0xCAC2;
    const CHUNK_TYPE_DONT_CARE: usize = 0xCAC3;
    const CHUNK_TYPE_CRC: usize = 0xCAC4;

    let chunk_structure = vec![
        ("chunk_type", "u16"),
        ("reserved", "u16"),
        ("output_block_count", "u32"),
        ("total_size", "u32"),
    ];

    let mut chonker = AndroidSparseChunkHeader {
        header_size: structures::common::size(&chunk_structure),
        ..Default::default()
    };

    // Sanity check available data
    if chunk_data.len() >= chonker.header_size {
        // Parse the header
        let chunk_header = structures::common::parse(chunk_data, &chunk_structure, "little");

        // Make sure the reserved field is zero
        if chunk_header["reserved"] == 0 {
            // Populate the structure values
            chonker.block_count = chunk_header["output_block_count"];
            chonker.data_size = chunk_header["total_size"] - chonker.header_size;
            chonker.is_crc = chunk_header["chunk_type"] == CHUNK_TYPE_CRC;
            chonker.is_raw = chunk_header["chunk_type"] == CHUNK_TYPE_RAW;
            chonker.is_fill = chunk_header["chunk_type"] == CHUNK_TYPE_FILL;
            chonker.is_dont_care = chunk_header["chunk_type"] == CHUNK_TYPE_DONT_CARE;

            // The chunk type must be one of the known chunk types
            if chonker.is_crc == true
                || chonker.is_raw == true
                || chonker.is_fill == true
                || chonker.is_dont_care == true
            {
                return Ok(chonker);
            }
        }
    }

    return Err(structures::common::StructureError);
}
