use crate::extractors;

/// Describes how to run the dmg2img utility to convert DMG images to MBR
pub fn dmg_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("dmg2img".to_string()),
        extension: "dmg".to_string(),
        arguments: vec![
            "-i".to_string(), // Input file
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            "-o".to_string(), // Output file
            "mbr.img".to_string(),
        ],
        exit_codes: vec![0, 1],
        ..Default::default()
    }
}
