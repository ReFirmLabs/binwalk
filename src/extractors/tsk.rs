use crate::extractors;

/// Describes how to run the tsk_recover utility to extract various file systems
pub fn tsk_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("tsk_recover".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            "-i".to_string(), // Set input type to "raw"
            "raw".to_string(),
            "-a".to_string(), // Only recover allocated files
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            "rootfs".to_string(), // Ouput directory
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
