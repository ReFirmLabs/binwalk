use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::riff::parse_riff_header;

/// Describes the internal RIFF image extactor
pub fn riff_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_riff_image),
        do_not_recurse: true,
        ..Default::default()
    }
}

/// Internal extractor for carving RIFF files to disk
pub fn extract_riff_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.riff";
    const WAV_OUTFILE_NAME: &str = "video.wav";
    const WAV_TYPE: &str = "WAVE";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Ok(riff_header) = parse_riff_header(&file_data[offset..]) {
        result.size = Some(riff_header.size);
        result.success = true;

        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);

            let file_path: String = if riff_header.chunk_type == WAV_TYPE {
                WAV_OUTFILE_NAME.to_string()
            } else {
                OUTFILE_NAME.to_string()
            };

            result.success = chroot.carve_file(file_path, file_data, offset, result.size.unwrap());
        }
    }

    result
}
