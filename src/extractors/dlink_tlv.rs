use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::dlink_tlv::parse_dlink_tlv_header;

/// Defines the internal extractor function for carving out D-Link TLV firmware images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dlink_tlv::dlink_tlv_extractor;
///
/// match dlink_tlv_extractor().utility {
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
pub fn dlink_tlv_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_dlink_tlv_image),
        ..Default::default()
    }
}

/// Internal extractor for carve pieces of D-Link TLV images to disk
pub fn extract_dlink_tlv_image(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTPUT_FILE_NAME: &str = "image.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Get the D-Link TLV image data
    if let Some(tlv_data) = file_data.get(offset..) {
        // Parse the TLV header
        if let Ok(tlv_header) = parse_dlink_tlv_header(tlv_data) {
            result.success = true;
            result.size = Some(tlv_header.header_size + tlv_header.data_size);

            // If extraction was requested, do it
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success = chroot.carve_file(
                    OUTPUT_FILE_NAME,
                    tlv_data,
                    tlv_header.header_size,
                    tlv_header.data_size,
                );
            }
        }
    }

    result
}
