use crate::structures::png::parse_png_chunk_header;
use crate::extractors::common::{ create_file, safe_path_join };
use crate::extractors::common::{ Extractor, ExtractorType, ExtractionResult };

// Defines the internal extractor function for carving out PNG images
pub fn png_extractor() -> Extractor {
    return Extractor { utility: ExtractorType::Internal(extract_png_image), ..Default::default() };
}

pub fn extract_png_image(file_data: &Vec<u8>, offset: usize, output_directory: Option<&String>) -> ExtractionResult {
    const PNG_HEADER_LEN: usize = 8;
    const OUTFILE_NAME: &str = "image.png";

    let mut result = ExtractionResult { ..Default::default() };

    // Parse all the PNG chunks to determine the size of PNG data; first chunk starts immediately after the 8-byte PNG header
    if let Some(png_data_size) = get_png_data_size(&file_data[offset+PNG_HEADER_LEN..]) {

        // Total size is the size of the header plus the size of the data
        result.size = Some(png_data_size + PNG_HEADER_LEN);
        result.success = true;

        // If extraction was requested, extract the PNG
        if let Some(outdir) = output_directory {
            let file_path = safe_path_join(outdir, &OUTFILE_NAME.to_string());
            result.success = create_file(&file_path, file_data, offset, result.size.unwrap());
        }
    }

    return result;
}

fn get_png_data_size(png_chunk_data: &[u8]) -> Option<usize> {
    
    let mut png_chunk_offset: usize = 0;

    // Loop until we run out of data
    while png_chunk_offset < png_chunk_data.len() {

        // Parse this PNG chunk header
        if let Ok(chunk_header) = parse_png_chunk_header(&png_chunk_data[png_chunk_offset..]) {

            // The next chunk header will start immediately after this chunk
            png_chunk_offset += chunk_header.total_size;

            // If this was the last chunk, then png_chunk_offset is the total size of the PNG data
            if chunk_header.is_last_chunk == true {
                return Some(png_chunk_offset);
            }
        }
    }

    return None;
}
