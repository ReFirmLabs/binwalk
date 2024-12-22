use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::dxbc::parse_dxbc_header;

/// Defines the internal extractor function for carving out DXBC images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dxbc::dxbc_extractor;
///
/// match dxbc_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn dxbc_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_dxbc_file),
        ..Default::default()
    }
}

pub fn extract_dxbc_file(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "shader.dxbc";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Ok(header) = parse_dxbc_header(&file_data[offset..]) {
        // Report success
        result.size = Some(header.size);
        result.success = true;

        // Do extraction, if requested
        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);
            result.success =
                chroot.carve_file(OUTFILE_NAME, file_data, offset, result.size.unwrap());
        }
    }

    result
}
