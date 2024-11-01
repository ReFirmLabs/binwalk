use crate::extractors;

/// Describes how to run the tar utility to extract tarball archives
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::tarball::tarball_extractor;
///
/// match tarball_extractor().utility {
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
pub fn tarball_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("tar".to_string()),
        extension: "tar".to_string(),
        arguments: vec![
            "-x".to_string(),
            "-f".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // Exit code may be 2 if attempting to create special device files fails
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}
