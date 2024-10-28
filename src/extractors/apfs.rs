use crate::extractors;

/// Describes how to run the 7zzs utility to extract APFS images
pub fn apfs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("7zzs".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            "x".to_string(),   // Perform extraction
            "-y".to_string(),  // Assume Yes to all questions
            "-o.".to_string(), // Output to current working directory
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // If there is trailing data after the compressed data, extraction will happen but exit code will be 2
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}
