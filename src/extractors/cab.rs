use crate::extractors;

/// Describes how to run the cabextract utility to extract MS CAB archives
pub fn cab_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("cabextract".to_string()),
        extension: "cab".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}
