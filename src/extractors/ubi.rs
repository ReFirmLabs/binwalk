use crate::extractors;

/// Describes how to run the ubireader_extract_images utility to extract UBI images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::ubi::ubi_extractor;
///
/// match ubi_extractor().utility {
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
pub fn ubi_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(
            "ubireader_extract_images".to_string(),
        ),
        extension: "img".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}

/// Describes how to run the ubireader_extract_files utility to extract UBIFS images
pub fn ubifs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("ubireader_extract_files".to_string()),
        extension: "ubifs".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}
