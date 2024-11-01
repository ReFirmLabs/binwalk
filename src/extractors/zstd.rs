use crate::extractors;

/// Describes how to run the zstd utility to extract ZSTD compressed files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::zstd::zstd_extractor;
///
/// match zstd_extractor().utility {
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
pub fn zstd_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("zstd".to_string()),
        extension: "zst".to_string(),
        arguments: vec![
            "-k".to_string(), // Don't delete input files (we do this ourselves)
            "-f".to_string(), // Force overwrite if output file, for some reason, exists (disables y/n prompts)
            "-d".to_string(), // Perform a decompression
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
