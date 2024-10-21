use crate::extractors;

/// Describes how to run the lzop utility to extract LZO compressed files
pub fn lzop_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("lzop".to_string()),
        extension: "lzo".to_string(),
        arguments: vec![
            "-p".to_string(), // Output to the current directory
            "-N".to_string(), // Restore original file name
            "-d".to_string(), // Perform a decompression
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
