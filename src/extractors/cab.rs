use crate::extractors;

/// Describes how to run the cabextract utility to extract MS CAB archives
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::cab::cab_extractor;
///
/// match cab_extractor().utility {
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
pub fn cab_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("cabextract".to_string()),
        extension: "cab".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}
