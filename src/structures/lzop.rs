use crate::structures;

const LZO_CHECKSUM_SIZE: usize = 4;

#[derive(Debug, Default, Clone)]
pub struct LZOPFileHeader {
    pub header_size: usize,
    pub block_checksum_present: bool,
}

pub fn parse_lzop_file_header(
    lzop_data: &[u8],
) -> Result<LZOPFileHeader, structures::common::StructureError> {
    const LZO_MAX_VERSION: usize = 0x1040;
    const LZO_HEADER_MAX_SIZE: usize = 313;

    const LZO_HEADER_SIZE_P1: usize = 21;
    const LZO_HEADER_SIZE_P2: usize = 13;

    const FILTER_SIZE: usize = 4;

    const FLAG_FILTER: usize = 0x000_00800;
    //const FLAG_CRC32_D: usize = 0x0000_0100;
    const FLAG_CRC32_C: usize = 0x0000_0200;
    //const FLAG_ADLER32_D: usize = 0x0000_0001;
    const FLAG_ADLER32_C: usize = 0x0000_0002;

    let lzo_structure_p1 = vec![
        ("magic_p1", "u8"),
        ("magic_p2", "u64"),
        ("version", "u16"),
        ("lib_version", "u16"),
        ("version_needed", "u16"),
        ("method", "u8"),
        ("level", "u8"),
        ("flags", "u32"),
    ];

    let lzo_structure_p2 = vec![
        ("mode", "u32"),
        ("mtime", "u32"),
        ("gmt_diff", "u32"),
        ("file_name_length", "u8"),
    ];

    let allowed_methods: Vec<usize> = vec![1, 2, 3];

    let mut lzop_info = LZOPFileHeader {
        ..Default::default()
    };

    // Sanity check the size of available data
    if lzop_data.len() >= LZO_HEADER_MAX_SIZE {
        // Parse the first part of the header
        let lzo_header_p1 =
            structures::common::parse(&lzop_data[0..LZO_HEADER_SIZE_P1], &lzo_structure_p1, "big");

        // Sanity check the methods field
        if allowed_methods.contains(&lzo_header_p1["method"]) {
            // Sanity check the header version numbers
            if lzo_header_p1["version"] <= LZO_MAX_VERSION
                && lzo_header_p1["version"] >= lzo_header_p1["version_needed"]
            {
                // Unless the optional filter field is included, start of the second part of the header is at the end of the first
                let mut header_p2_start: usize = LZO_HEADER_SIZE_P1;

                // Next part of the header may or may not have an optional filter field
                if (lzo_header_p1["flags"] & FLAG_FILTER) != 0 {
                    header_p2_start += FILTER_SIZE;
                }

                // Calculate the end of the second part of the header
                let header_p2_end: usize = header_p2_start + LZO_HEADER_SIZE_P2;

                // Parse the second part of the header
                let lzo_header_p2 = structures::common::parse(
                    &lzop_data[header_p2_start..header_p2_end],
                    &lzo_structure_p2,
                    "big",
                );

                // Calculate the total header size; compressed data blocks will immediately follow
                lzop_info.header_size =
                    header_p2_end + lzo_header_p2["file_name_length"] + LZO_CHECKSUM_SIZE;

                // Check if block headers include an optional compressed data checksum field
                lzop_info.block_checksum_present =
                    (lzo_header_p1["flags"] & FLAG_ADLER32_C & FLAG_CRC32_C) != 0;

                // Sanity check on the calculated header size
                if lzop_info.header_size <= lzop_data.len() {
                    return Ok(lzop_info);
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct LZOPBlockHeader {
    pub header_size: usize,
    pub compressed_size: usize,
    pub uncompressed_size: usize,
    pub checksum_size: usize,
}

// Parse the LZO blocks to determine the size of the compressed data
pub fn parse_lzop_block_header(
    lzo_data: &[u8],
    compressed_checksum_present: bool,
) -> Result<LZOPBlockHeader, structures::common::StructureError> {
    const BLOCK_HEADER_SIZE: usize = 12;
    const MAX_UNCOMPRESSED_BLOCK_SIZE: usize = 64 * 1024 * 1024;

    let block_structure = vec![
        ("uncompressed_size", "u32"),
        ("compressed_size", "u32"),
        ("uncompressed_checksum", "u32"),
    ];

    if lzo_data.len() >= BLOCK_HEADER_SIZE {
        // Parse the block header
        let block_header =
            structures::common::parse(&lzo_data[0..BLOCK_HEADER_SIZE], &block_structure, "big");

        // Basic sanity check on the block header values
        if block_header["compressed_size"] != 0
            && block_header["uncompressed_size"] != 0
            && block_header["uncompressed_checksum"] != 0
            && block_header["uncompressed_size"] <= MAX_UNCOMPRESSED_BLOCK_SIZE
        {
            let mut block_hdr_info = LZOPBlockHeader {
                ..Default::default()
            };

            block_hdr_info.header_size = BLOCK_HEADER_SIZE;
            block_hdr_info.compressed_size = block_header["compressed_size"];
            block_hdr_info.uncompressed_size = block_header["uncompressed_size"];

            if compressed_checksum_present {
                block_hdr_info.checksum_size = LZO_CHECKSUM_SIZE;
            }

            return Ok(block_hdr_info);
        }
    }

    return Err(structures::common::StructureError);
}

/*
 * Parsers and validates the LZOP EOF marker.
 * Returns the size of the EOF marker upon success.
 */
pub fn parse_lzop_eof_marker(eof_data: &[u8]) -> Result<usize, structures::common::StructureError> {
    const EOF_MARKER: usize = 0;
    const EOF_MARKER_SIZE: usize = 4;

    let eof_structure = vec![("marker", "u32")];

    /*
     * It is unclear, but observed, that LZOP files end with 0x00000000; this is assumed to be an EOF marker,
     * as other similar compression file formats use that. This assumption could be incorrect.
     *
     * Make sure that there are enough remaining bytes for this expected marker, and then validate that it is 0.
     */
    if eof_data.len() >= EOF_MARKER_SIZE {
        // Parse the EOF marker
        let eof_marker =
            structures::common::parse(&eof_data[0..EOF_MARKER_SIZE], &eof_structure, "big");

        // Sanity check the EOF marker
        if eof_marker["marker"] == EOF_MARKER {
            // Return the size of the EOF marker
            return Ok(EOF_MARKER_SIZE);
        }
    }

    return Err(structures::common::StructureError);
}
