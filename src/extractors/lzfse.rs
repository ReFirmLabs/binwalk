use crate::extractors::common::{Extractor, ExtractorType, SOURCE_FILE_PLACEHOLDER};

/// Describes how to run the lzfse utility to decompress LZFSE files
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
