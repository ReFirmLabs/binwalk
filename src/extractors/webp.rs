use crate::extractors::common::{create_file, safe_path_join};
use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::structures::webp::parse_webp_header;

pub fn webp_extractor() -> Extractor {
    return Extractor {
        utility: ExtractorType::Internal(extract_webp_image),
        do_not_recurse: true,
        ..Default::default()
    };
}

pub fn extract_webp_image(
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.webp";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Ok(webp_header) = parse_webp_header(&file_data[offset..]) {
        result.size = Some(webp_header.size);
        result.success = true;

        if let Some(outdir) = output_directory {
            let file_path = safe_path_join(outdir, &OUTFILE_NAME.to_string());
            result.success = create_file(&file_path, file_data, offset, result.size.unwrap());
        }
    }

    return result;
}
