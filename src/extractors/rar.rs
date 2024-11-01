use crate::extractors;

/// Describes how to run the unrar utility to extract RAR archives
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::rar::rar_extractor;
///
/// match rar_extractor().utility {
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
pub fn rar_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("unrar".to_string()),
        extension: "rar".to_string(),
        arguments: vec![
            "x".to_string(),  // Perform extraction
            "-y".to_string(), // Answer yes to all questions
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
