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
    const HEADER_SIZE: usize = 2;
    return inflate::inflate_decompressor(file_data, offset + HEADER_SIZE, output_directory);
}
