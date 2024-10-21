use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::inflate;
use crate::structures::gzip::parse_gzip_header;

/// Defines the internal extractor function for decompressing gzip data
pub fn gzip_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(gzip_decompress),
        ..Default::default()
    }
}

/// Internal extractor for gzip compressed data
pub fn gzip_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Parse the gzip header
    if let Ok(gzip_header) = parse_gzip_header(&file_data[offset..]) {
        // Deflate compressed data starts at the end of the gzip header
        let deflate_data_start: usize = offset + gzip_header.size;

        if file_data.len() > deflate_data_start {
            return inflate::inflate_decompressor(file_data, deflate_data_start, output_directory);
        }
    }

    // Return failure
    ExtractionResult {
        ..Default::default()
    }
}
