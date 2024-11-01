use crate::extractors;

/// Describes how to run the jefferson utility to extract JFFS file systems
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::jffs2::jffs2_extractor;
///
/// match jffs2_extractor().utility {
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
pub fn jffs2_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("jefferson".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            "-f".to_string(), // Force overwrite if output file, for some reason, exists
            "-d".to_string(), // Output to jffs2-root directory
            "jffs2-root".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0, 1, 2],
        ..Default::default()
    }
}
