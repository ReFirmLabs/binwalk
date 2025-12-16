use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::tiff::get_tiff_size;

/// Defines the internal extractor function for carving out TIFF images
pub fn tiff_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_tiff_image),
        ..Default::default()
    }
}

/// Internal extractor for carving TIFF images to disk
pub fn extract_tiff_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.tiff";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Find the TIFF size
    if let Ok(size) = get_tiff_size(&file_data[offset..]) {
        result.size = Some(size);
        result.success = true;

        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);
            result.success =
                chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
        }
    }

    result
}
