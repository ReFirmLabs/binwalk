use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::png::parse_png_chunk_header;

/// Defines the internal extractor function for carving out PNG images
pub fn png_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_png_image),
        ..Default::default()
    }
}

/// Internal extractor for carving PNG files to disk
pub fn extract_png_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const PNG_HEADER_LEN: usize = 8;
    const OUTFILE_NAME: &str = "image.png";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse all the PNG chunks to determine the size of PNG data; first chunk starts immediately after the 8-byte PNG header
    if let Some(png_data) = file_data.get(offset + PNG_HEADER_LEN..) {
        if let Some(png_data_size) = get_png_data_size(png_data) {
            // Total size is the size of the header plus the size of the data
            result.size = Some(png_data_size + PNG_HEADER_LEN);
            result.success = true;

            // If extraction was requested, extract the PNG
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success =
                    chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
            }
        }
    }

    result
}

fn get_png_data_size(png_chunk_data: &[u8]) -> Option<usize> {
    let available_data = png_chunk_data.len();
    let mut png_chunk_offset: usize = 0;
    let mut previous_png_chunk_offset = None;

    // Loop until we run out of data
    while is_offset_safe(available_data, png_chunk_offset, previous_png_chunk_offset) {
        // Parse this PNG chunk header
        if let Ok(chunk_header) = parse_png_chunk_header(&png_chunk_data[png_chunk_offset..]) {
            // The next chunk header will start immediately after this chunk
            previous_png_chunk_offset = Some(png_chunk_offset);
            png_chunk_offset += chunk_header.total_size;

            // If this was the last chunk, then png_chunk_offset is the total size of the PNG data
            if chunk_header.is_last_chunk {
                return Some(png_chunk_offset);
            }
        }
    }

    None
}
