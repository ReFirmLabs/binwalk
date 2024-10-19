use crate::extractors;

/// Describes how to run the dumpifs utility to extract QNX IFS images
pub fn dumpifs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("dumpifs".to_string()),
        extension: "ifs".to_string(),
        arguments: vec![
            "-x".to_string(), // Extract the image
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
