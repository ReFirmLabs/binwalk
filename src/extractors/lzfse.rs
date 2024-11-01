use crate::extractors::common::{Extractor, ExtractorType, SOURCE_FILE_PLACEHOLDER};

/// Describes how to run the lzfse utility to decompress LZFSE files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::lzfse::lzfse_extractor;
///
/// match lzfse_extractor().utility {
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
pub fn lzfse_extractor() -> Extractor {
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";

    Extractor {
        utility: ExtractorType::External("lzfse".to_string()),
        extension: "bin".to_string(),
        arguments: vec![
            "-decode".to_string(), // Do decompression
            "-i".to_string(),      // Input file
            SOURCE_FILE_PLACEHOLDER.to_string(),
            "-o".to_string(), // Output file
            OUTPUT_FILE_NAME.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
