use crate::common::crc32;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::jboot::parse_jboot_sch2_header;

/// Defines the internal extractor function for carving out JBOOT SCH2 kernels
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::jboot::sch2_extractor;
///
/// match sch2_extractor().utility {
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
pub fn sch2_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_jboot_sch2_kernel),
        ..Default::default()
    }
}

/// Extract the kernel described by a JBOOT SCH2 header
pub fn extract_jboot_sch2_kernel(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // Output file name
    const OUTFILE_NAME: &str = "kernel.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Get the SCH2 data
    if let Some(sch2_header_data) = file_data.get(offset..) {
        // Parse the SCH2 header
        if let Ok(sch2_header) = parse_jboot_sch2_header(sch2_header_data) {
            let kernel_start: usize = offset + sch2_header.header_size;
            let kernel_end: usize = kernel_start + sch2_header.kernel_size;

            // Validate the kernel data checksum
            if let Some(kernel_data) = file_data.get(kernel_start..kernel_end) {
                if crc32(kernel_data) == (sch2_header.kernel_checksum as u32) {
                    // Everything checks out ok
                    result.size = Some(sch2_header.header_size + sch2_header.kernel_size);
                    result.success = true;

                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);
                        result.success = chroot.carve_file(
                            OUTFILE_NAME,
                            file_data,
                            kernel_start,
                            sch2_header.kernel_size,
                        );
                    }
                }
            }
        }
    }

    result
}
