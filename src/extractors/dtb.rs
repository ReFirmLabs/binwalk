use crate::extractors;

/// Describes how to run the dtc utility to extract DTB files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dtb::dtb_extractor;
///
/// match dtb_extractor().utility {
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
pub fn dtb_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("dtc".to_string()),
        extension: "dtb".to_string(),
        arguments: vec![
            "-I".to_string(), // Input type: dtb
            "dtb".to_string(),
            "-O".to_string(), // Output type: dts
            "dts".to_string(),
            "-o".to_string(), // Output file name: system.dtb
            "system.dtb".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
