use crate::extractors;

/// Describes how to run the lz4 utility to extract LZ4 compressed files
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
