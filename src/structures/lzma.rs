use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct LZMAHeader {
    pub properties: usize,
    pub dictionary_size: usize,
    pub decompressed_size: usize,
}

pub fn parse_lzma_header(
    lzma_data: &[u8],
) -> Result<LZMAHeader, structures::common::StructureError> {
    const LZMA_STREAM_SIZE: usize = 0xFFFFFFFFFFFFFFFF;
    const MIN_SUPPORTED_DECOMPRESSED_SIZE: usize = 256;
    const MAX_SUPPORTED_DECOMPRESSED_SIZE: usize = 0xFFFFFFFF;

    let lzma_structure = vec![
        ("properties", "u8"),
        ("dictionary_size", "u32"),
        ("decompressed_size", "u64"),
        ("null_byte", "u8"),
    ];

    let available_data = lzma_data.len();
    let mut lzma_hdr_info = LZMAHeader {
        ..Default::default()
    };
    let lzma_header_size: usize = structures::common::size(&lzma_structure);

    // Sanity check the size of available data
    if available_data > lzma_header_size {
        // Parse the lzma header
        let lzma_header =
            structures::common::parse(&lzma_data[0..lzma_header_size], &lzma_structure, "little");

        // Sanity check expected values for LZMA header fields
        if lzma_header["null_byte"] == 0 {
            if lzma_header["decompressed_size"] > MIN_SUPPORTED_DECOMPRESSED_SIZE {
                if lzma_header["decompressed_size"] == LZMA_STREAM_SIZE
                    || lzma_header["decompressed_size"] < MAX_SUPPORTED_DECOMPRESSED_SIZE
                {
                    lzma_hdr_info.properties = lzma_header["properties"];
                    lzma_hdr_info.dictionary_size = lzma_header["dictionary_size"];
                    lzma_hdr_info.decompressed_size = lzma_header["decompressed_size"];

                    return Ok(lzma_hdr_info);
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}
