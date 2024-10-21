use crate::extractors;

/// Describes how to run the unyaffs utility to extract YAFFS2 file systems
pub fn yaffs2_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("unyaffs".to_string()),
        extension: "img".to_string(),
        arguments: vec![
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            "yaffs-root".to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
