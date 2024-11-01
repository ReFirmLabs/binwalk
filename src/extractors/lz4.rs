use crate::extractors;

/// Describes how to run the lz4 utility to extract LZ4 compressed files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::lz4::lz4_extractor;
///
/// match lz4_extractor().utility {
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
pub fn lz4_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("lz4".to_string()),
        extension: "lz4".to_string(),
        arguments: vec![
            "-f".to_string(), // Force overwirte if, for some reason, the output file exists
            "-d".to_string(), // Perform a decompression
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            "decompressed.bin".to_string(), // Output file
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
