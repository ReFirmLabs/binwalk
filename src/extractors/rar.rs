use crate::extractors;

/// Describes how to run the unrar utility to extract RAR archives
pub fn rar_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("unrar".to_string()),
        extension: "rar".to_string(),
        arguments: vec![
            "x".to_string(),  // Perform extraction
            "-y".to_string(), // Answer yes to all questions
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
