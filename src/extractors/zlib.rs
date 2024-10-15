use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::inflate;

/// Defines the internal extractor function for decompressing zlib data
pub fn zlib_extractor() -> Extractor {
    return Extractor {
        utility: ExtractorType::Internal(zlib_decompress),
        ..Default::default()
    };
}

/// Internal extractor for decompressing ZLIB data
pub fn zlib_decompress(
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Size of the zlib header
    const HEADER_SIZE: usize = 2;
    // Size of the checksum that follows the deflate data stream
    const CHECKSUM_SIZE: usize = 4;

    // Do the decompression, ignoring the ZLIB header
    let mut result =
        inflate::inflate_decompressor(file_data, offset + HEADER_SIZE, output_directory);

    // If the decompression reported the size of the deflate data, update the reported size
    // to include the ZLIB header and checksum fields
    if let Some(deflate_size) = result.size {
        result.size = Some(HEADER_SIZE + deflate_size + CHECKSUM_SIZE);
    }

    return result;
}
