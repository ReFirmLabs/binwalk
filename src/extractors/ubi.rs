use crate::extractors;

/// Describes how to run the ubireader_extract_images utility to extract UBI images
pub fn ubi_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(
            "ubireader_extract_images".to_string(),
        ),
        extension: "img".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}

/// Describes how to run the ubireader_extract_files utility to extract UBIFS images
pub fn ubifs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("ubireader_extract_files".to_string()),
        extension: "ubifs".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}
