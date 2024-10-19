use crate::extractors;

/// Describes how to run the jefferson utility to extract JFFS file systems
pub fn jffs2_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("jefferson".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            "-f".to_string(), // Force overwrite if output file, for some reason, exists
            "-d".to_string(), // Output to jffs2-root directory
            "jffs2-root".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0, 1, 2],
        ..Default::default()
    }
}
