use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct ZSTDHeader {
    pub fixed_header_size: usize,
    pub dictionary_id_flag: usize,
    pub content_checksum_present: bool,
    pub single_segment_flag: bool,
    pub frame_content_flag: usize,
}

pub fn parse_zstd_header(
    zstd_data: &[u8],
) -> Result<ZSTDHeader, structures::common::StructureError> {
    const ZSTD_HEADER_MIN_SIZE: usize = 5;
    const FRAME_UNUSED_BITS_MASK: usize = 0b00011000;
    const DICTIONARY_ID_MASK: usize = 0b11;
    const CONTENT_CHECKSUM_MASK: usize = 0b100;
    const SINGLE_SEGMENT_MASK: usize = 0b100000;
    const FRAME_CONTENT_MASK: usize = 0b11000000;
    const FRAME_CONTENT_SHIFT: usize = 6;

    let zstd_header_structure = vec![("magic", "u32"), ("frame_header_descriptor", "u8")];

    let mut zstd_info = ZSTDHeader {
        fixed_header_size: ZSTD_HEADER_MIN_SIZE,
        ..Default::default()
    };

    // Sanity check the size of available data
    if zstd_data.len() >= ZSTD_HEADER_MIN_SIZE {
        // Parse the ZSTD header
        let zstd_header = structures::common::parse(
            &zstd_data[0..ZSTD_HEADER_MIN_SIZE],
            &zstd_header_structure,
            "little",
        );

        // Unused bits should be unused
        if (zstd_header["frame_header_descriptor"] & FRAME_UNUSED_BITS_MASK) == 0 {
            // Indicates if a dictionary ID field is present, and if so, how big it is
            zstd_info.dictionary_id_flag =
                zstd_header["frame_header_descriptor"] & DICTIONARY_ID_MASK;

            // Indicates if there is a 4-byte checksum present at the end of the compressed block stream
            zstd_info.content_checksum_present =
                (zstd_header["frame_header_descriptor"] & CONTENT_CHECKSUM_MASK) != 0;

            // If this flag is set, then the window descriptor byte is not present
            zstd_info.single_segment_flag =
                (zstd_header["frame_header_descriptor"] & SINGLE_SEGMENT_MASK) != 0;

            // Indicates if the frame content field is present, and if so, how big it is
            zstd_info.frame_content_flag = (zstd_header["frame_header_descriptor"]
                & FRAME_CONTENT_MASK)
                >> FRAME_CONTENT_SHIFT;

            return Ok(zstd_info);
        }
    }

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct ZSTDBlockHeader {
    pub header_size: usize,
    pub block_type: usize,
    pub block_size: usize,
    pub last_block: bool,
}

pub fn parse_block_header(
    block_data: &[u8],
) -> Result<ZSTDBlockHeader, structures::common::StructureError> {
    const ZSTD_BLOCK_HEADER_SIZE: usize = 3;
    const ZSTD_BLOCK_TYPE_MASK: usize = 0b110;
    const ZSTD_BLOCK_TYPE_SHIFT: usize = 1;
    const ZSTD_RLE_BLOCK_TYPE: usize = 1;
    const ZSTD_RESERVED_BLOCK_TYPE: usize = 3;
    const ZSTD_LAST_BLOCK_MASK: usize = 0b1;
    const ZSTD_BLOCK_SIZE_MASK: usize = 0b1111_1111_1111_1111_1111_1000;
    const ZSTD_BLOCK_SIZE_SHIFT: usize = 3;

    let zstd_block_header_structure = vec![("info_bits", "u24")];

    let mut block_info = ZSTDBlockHeader {
        header_size: ZSTD_BLOCK_HEADER_SIZE,
        ..Default::default()
    };

    if block_data.len() >= ZSTD_BLOCK_HEADER_SIZE {
        // Parse the block header
        let block_header =
            structures::common::parse(block_data, &zstd_block_header_structure, "little");

        // Interpret the bit fields of the block header, which indicate the type of block, the size of the block, and if this is the last block
        block_info.last_block = (block_header["info_bits"] & ZSTD_LAST_BLOCK_MASK) != 0;
        block_info.block_type =
            (block_header["info_bits"] & ZSTD_BLOCK_TYPE_MASK) >> ZSTD_BLOCK_TYPE_SHIFT;
        block_info.block_size =
            (block_header["info_bits"] & ZSTD_BLOCK_SIZE_MASK) >> ZSTD_BLOCK_SIZE_SHIFT;

        /*
         * An RLE block consists of a single byte of raw block data, which when decompressed must be repeased block_size times.
         * We're not decompressing, just want to know the size of the raw data so we can check the next block header.
         *
         * Reserved block types should not be encountered, and are considered an error during decompression.
         */
        if block_info.block_type == ZSTD_RLE_BLOCK_TYPE {
            block_info.block_size = 1;
        }

        // Block type is invalid if set to the reserved block type
        if block_info.block_type != ZSTD_RESERVED_BLOCK_TYPE {
            return Ok(block_info);
        }
    }

    return Err(structures::common::StructureError);
}
