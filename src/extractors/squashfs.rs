use crate::extractors;

/// Describes how to run the sasquatch utility to extract SquashFS images,
/// with unsquashfs as a fallback for systems that only have the standard tool.
pub fn squashfs_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("sasquatch".to_string()),
        extension: "sqsh".to_string(),
        arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
        // Exit code may be 0 or 2; 2 indicates running as not root, but otherwise extraction is ok
        exit_codes: vec![0, 2],
        // Fall back to unsquashfs if sasquatch is not installed
        fallback: Some(Box::new(extractors::common::Extractor {
            utility: extractors::common::ExtractorType::External("unsquashfs".to_string()),
            extension: "sqsh".to_string(),
            arguments: vec![extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()],
            exit_codes: vec![0, 2],
            ..Default::default()
        })),
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
