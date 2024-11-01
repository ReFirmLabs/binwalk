use crate::extractors;

/// Describes how to run the dumpifs utility to extract QNX IFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dumpifs::dumpifs_extractor;
///
/// match dumpifs_extractor().utility {
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
pub fn dumpifs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("dumpifs".to_string()),
        extension: "ifs".to_string(),
        arguments: vec![
            "-x".to_string(), // Extract the image
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
