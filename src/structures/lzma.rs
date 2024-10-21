use crate::structures::common::{self, StructureError};

/// Struct to store useful LZMA header data
#[derive(Debug, Default, Clone)]
pub struct LZMAHeader {
    pub properties: usize,
    pub dictionary_size: usize,
    pub decompressed_size: usize,
}

/// Parse an LZMA header
pub fn parse_lzma_header(lzma_data: &[u8]) -> Result<LZMAHeader, StructureError> {
    // Streamed data has a reported size of -1
    const LZMA_STREAM_SIZE: usize = 0xFFFFFFFFFFFFFFFF;

    // Some sane min and max values on the reported decompressed data size
    const MIN_SUPPORTED_DECOMPRESSED_SIZE: usize = 256;
    const MAX_SUPPORTED_DECOMPRESSED_SIZE: usize = 0xFFFFFFFF;

    let lzma_structure = vec![
        ("properties", "u8"),
        ("dictionary_size", "u32"),
        ("decompressed_size", "u64"),
        ("null_byte", "u8"),
    ];

    let mut lzma_hdr_info = LZMAHeader {
        ..Default::default()
    };

    // Parse the lzma header
    if let Ok(lzma_header) = common::parse(lzma_data, &lzma_structure, "little") {
        // Make sure the expected NULL byte is NULL
        if lzma_header["null_byte"] == 0 {
            // Sanity check the reported decompressed size
            if lzma_header["decompressed_size"] >= MIN_SUPPORTED_DECOMPRESSED_SIZE
                && (lzma_header["decompressed_size"] == LZMA_STREAM_SIZE
                    || lzma_header["decompressed_size"] <= MAX_SUPPORTED_DECOMPRESSED_SIZE)
            {
                lzma_hdr_info.properties = lzma_header["properties"];
                lzma_hdr_info.dictionary_size = lzma_header["dictionary_size"];
                lzma_hdr_info.decompressed_size = lzma_header["decompressed_size"];

                return Ok(lzma_hdr_info);
            }
        }
    }

    Err(StructureError)
}
