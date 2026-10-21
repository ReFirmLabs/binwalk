use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::dex::parse_dex_header;

/// Defines the internal extractor for DEX files
pub fn dex_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_dex_file),
        ..Default::default()
    }
}

/// Extracts a DEX file from the specified offset
pub fn extract_dex_file(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "classes.dex";

    let mut result = ExtractionResult {
        ..Default::default()
    };
    result.success = false;

    // Parse the DEX header.
    if let Some(data) = file_data.get(offset..) {
        if let Ok(dex_header) = parse_dex_header(data) {
            result.size = Some(dex_header.file_size);
            result.success = true;

            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success =
                    chroot.carve_file(OUTFILE_NAME, file_data, offset, dex_header.file_size);
            }
        }
    }

    result
}