use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::matter_ota::parse_matter_ota_header;

/// Defines the internal extractor function for extracting a Matter OTA firmware payload */
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::matter_ota::matter_ota_extractor;
///
/// match matter_ota_extractor().utility {
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
pub fn matter_ota_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_matter_ota),
        ..Default::default()
    }
}

/// Matter OTA firmware payload extractor
pub fn extract_matter_ota(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "matter_payload.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Ok(ota_header) = parse_matter_ota_header(&file_data[offset..]) {
        const MAGIC_SIZE: usize = 4;
        const TOTAL_SIZE_SIZE: usize = 8;
        const HEADER_SIZE_SIZE: usize = 4;

        let total_header_size =
            MAGIC_SIZE + TOTAL_SIZE_SIZE + HEADER_SIZE_SIZE + ota_header.header_size;

        result.success = true;
        result.size = Some(ota_header.total_size);

        let payload_start = offset + total_header_size;
        let payload_end = offset + total_header_size + ota_header.payload_size;

        // Sanity check reported payload size and get the payload data
        if let Some(payload_data) = file_data.get(payload_start..payload_end) {
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success =
                    chroot.carve_file(OUTFILE_NAME, payload_data, 0, payload_data.len());
            }
        }
    }

    result
}
