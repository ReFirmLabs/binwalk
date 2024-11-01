use crate::extractors;

/// Describes how to run the uefi-firmware-parser utility to extract UEFI images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::uefi::uefi_extractor;
///
/// match uefi_extractor().utility {
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
pub fn uefi_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("uefi-firmware-parser".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            "-o.".to_string(), // Output to the current working directory
            "-q".to_string(),  // Don't print verbose output
            "-e".to_string(),  // Extract
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        /*
         * This extractor recursively pulls out all the UEFI stuff *and* leaves raw copies of the extracted data on disk.
         * Recursing into this data would result in double extractions for no good reason.
         */
        do_not_recurse: true,
    }
}
