use crate::structures::common::{self, StructureError};
use xxhash_rust;

/// Struct to store LZ4 file header info
#[derive(Debug, Default, Clone)]
pub struct LZ4FileHeader {
    pub header_size: usize,
    pub block_checksum_present: bool,
    pub content_checksum_present: bool,
}

/// Parse an LZ4 file header
pub fn parse_lz4_file_header(lz4_data: &[u8]) -> Result<LZ4FileHeader, StructureError> {
    // Fixed size constants
    const MAGIC_SIZE: usize = 4;
    const LZ4_STRUCT_SIZE: usize = 6;

    const BD_RESERVED_MASK: usize = 0b10001111;
    const FLAGS_RESERVED_MASK: usize = 0b00000010;

    const FLAG_DICTIONARY_PRESENT: usize = 0b00000001;
    const FLAG_CONTENT_SIZE_PRESENT: usize = 0b00001000;
    const FLAG_BLOCK_CHECKSUM_PRESENT: usize = 0b00010000;
    const FLAG_CONTENT_CHECKSUM_PRESENT: usize = 0b00000100;

    const DICTIONARY_LEN: usize = 4;
    const CONTENT_SIZE_LEN: usize = 8;

    // Basic LZ4 header; optional fields and header CRC byte follow
    let lz4_structure = vec![("magic", "u32"), ("flags", "u8"), ("bd", "u8")];

    let mut lz4_hdr_info = LZ4FileHeader {
        ..Default::default()
    };

    // Parse the header
    if let Ok(lz4_header) = common::parse(lz4_data, &lz4_structure, "little") {
        // Make sure the reserved bits aren't set
        if (lz4_header["flags"] & FLAGS_RESERVED_MASK) == 0
            && (lz4_header["bd"] & BD_RESERVED_MASK) == 0
        {
            /*
             * Calculate the start and end of data used to calculate the header CRC.
             * CRC is calculated over the entire descriptor frame, including optional fields,
             * but does not include the magic bytes.
             */
            let crc_data_start: usize = MAGIC_SIZE;
            let mut crc_data_end: usize = crc_data_start + (LZ4_STRUCT_SIZE - MAGIC_SIZE);

            // If the optional content size field is present, the CRC field is pushed back after the content size field
            if (lz4_header["flags"] & FLAG_CONTENT_SIZE_PRESENT) != 0 {
                crc_data_end += CONTENT_SIZE_LEN;
            }

            // If the optional dictionary ID field is present, the CRC field is pushed back after the dictionary ID field
            if (lz4_header["flags"] & FLAG_DICTIONARY_PRESENT) != 0 {
                crc_data_end += DICTIONARY_LEN;
            }

            // Get the data over which the CRC is calculated
            if let Some(crc_data) = lz4_data.get(crc_data_start..crc_data_end) {
                // Grab the header CRC value stored in the file header (one byte only)
                if let Some(actual_crc) = lz4_data.get(crc_data_end) {
                    // Calculate the header CRC, which is the second byte of the xxh32 hash. It is calculated over the header, excluding the magic bytes.
                    let calculated_crc: u8 =
                        ((xxhash_rust::xxh32::xxh32(crc_data, 0) >> 8) & 0xFF) as u8;

                    // Make sure the CRC's match
                    if *actual_crc == calculated_crc {
                        // Data blocks start immediately after the header checksum byte
                        lz4_hdr_info.header_size = crc_data_end + 1;
                        lz4_hdr_info.block_checksum_present =
                            (lz4_header["flags"] & FLAG_BLOCK_CHECKSUM_PRESENT) != 0;
                        lz4_hdr_info.content_checksum_present =
                            (lz4_header["flags"] & FLAG_CONTENT_CHECKSUM_PRESENT) != 0;

                        return Ok(lz4_hdr_info);
                    }
                }
            }
        }
    }

    Err(StructureError)
}

/// Struct to store LZ4 block header info
#[derive(Debug, Default, Clone)]
pub struct LZ4BlockHeader {
    pub data_size: usize,
    pub header_size: usize,
    pub checksum_size: usize,
    pub last_block: bool,
}

/// Parse an LZ4 block header
pub fn parse_lz4_block_header(
    lz4_block_data: &[u8],
    checksum_present: bool,
) -> Result<LZ4BlockHeader, StructureError> {
    // Useful constants
    const SIZE_MASK: u32 = 0x7FFFFFFF;
    const END_MARKER: usize = 0;
    const CHECKSUM_SIZE: usize = 4;
    const BLOCK_STRUCT_SIZE: usize = 4;

    // Block headers are just a u32 size field
    let block_structure = vec![("block_size", "u32")];

    let mut lz4_block = LZ4BlockHeader {
        ..Default::default()
    };

    // Parse the block header
    if let Ok(block_header) = common::parse(lz4_block_data, &block_structure, "little") {
        // Header size is always 4 bytes
        lz4_block.header_size = BLOCK_STRUCT_SIZE;

        // If file size is 0, this is the end of the LZ4 data
        lz4_block.last_block = block_header["block_size"] == END_MARKER;

        // If a checksum is present, it will be an extra 4 bytes at the end of the block
        if checksum_present {
            lz4_block.checksum_size = CHECKSUM_SIZE;
        }

        // The high bit of the reported block size is not part of the actual block size
        lz4_block.data_size = ((block_header["block_size"] as u32) & SIZE_MASK) as usize;

        return Ok(lz4_block);
    }

    Err(StructureError)
}
