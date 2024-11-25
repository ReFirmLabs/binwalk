use crate::extractors;

/// Describes how to run the srec_cat utility to convert Motorola S-records to binary
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::srec::srec_extractor;
///
/// match srec_extractor().utility {
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
pub fn srec_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("srec_cat".to_string()),
        extension: "hex".to_string(),
        arguments: vec![
            "-output".to_string(),
            "s-record.bin".to_string(),
            "-binary".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
