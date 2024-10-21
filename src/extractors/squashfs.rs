use crate::extractors;

/// Describes how to run the sasquatch utility to extract SquashFS images
pub fn squashfs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("sasquatch".to_string()),
        extension: "sqsh".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        // Exit code may be 0 or 2; 2 indicates running as not root, but otherwise extraction is ok
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the sasquatch-v4be utility to extract big endian SquashFSv4 images
pub fn squashfs_v4_be_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("sasquatch-v4be".to_string()),
        extension: "sqsh".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        // Exit code may be 0 or 2; 2 indicates running as not root, but otherwise extraction is ok
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}
