use crate::extractors;

/// Describes how to run the unzip utility to extract ZIP archives
pub fn zip_extractor() -> extractors::common::Extractor {
    return extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("unzip".to_string()),
        extension: "zip".to_string(),
        arguments: vec![
            "-o".to_string(), // Overwrite files without prompting
            "-P".to_string(), // Specify a password for encrypted ZIP files
            "''".to_string(), // Just use a blank password
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // Exit code 2 occurs when a CRC fails; files are still extracted though
        exit_codes: vec![0, 2],
        ..Default::default()
    };
}
