use crate::extractors;

/// Describes how to run the tar utility to extract tarball archives
pub fn tarball_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("tar".to_string()),
        extension: "tar".to_string(),
        arguments: vec![
            "-x".to_string(),
            "-f".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // Exit code may be 2 if attempting to create special device files fails
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}
