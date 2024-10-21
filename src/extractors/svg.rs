use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::svg::parse_svg_image;

/// Defines the internal extractor function for carving out SVG images
pub fn svg_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_svg_image),
        ..Default::default()
    }
}

/// Internal extractor for carving SVG images to disk
pub fn extract_svg_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "image.svg";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the SVG image to determine its total size
    if let Ok(svg_image) = parse_svg_image(&file_data[offset..]) {
        result.size = Some(svg_image.total_size);
        result.success = true;

        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);
            result.success =
                chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
        }
    }

    result
}
