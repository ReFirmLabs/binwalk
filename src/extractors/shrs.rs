use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::shrs::parse_shrs_header;

/// Defines the internal extractor function for carving out D-Link SHRS firmware images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::shrs::shrs_extractor;
///
/// match shrs_extractor().utility {
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
pub fn shrs_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_shrs_image),
        ..Default::default()
    }
}

/// Internal extractor for carve pieces of encrypted SHRS firmware images to disk
pub fn extract_shrs_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const IV_FILE_NAME: &str = "iv.bin";
    const ENCRYPTED_FILE_NAME: &str = "encrypted.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the header
    if let Some(shrs_header_data) = file_data.get(offset..) {
        if let Ok(shrs_header) = parse_shrs_header(shrs_header_data) {
            result.success = true;
            result.size = Some(shrs_header.header_size + shrs_header.data_size);

            // Carve out the IV and encrypted data blob
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);

                if !chroot.create_file(IV_FILE_NAME, &shrs_header.iv)
                    || !chroot.carve_file(
                        ENCRYPTED_FILE_NAME,
                        file_data,
                        shrs_header.header_size,
                        shrs_header.data_size,
                    )
                {
                    result.success = false;
                }
            }
        }
    }

    result
}
