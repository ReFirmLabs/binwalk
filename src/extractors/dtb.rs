use crate::extractors;

/// Describes how to run the dtc utility to extract DTB files
pub fn dtb_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("dtc".to_string()),
        extension: "dtb".to_string(),
        arguments: vec![
            "-I".to_string(), // Input type: dtb
            "dtb".to_string(),
            "-O".to_string(), // Output type: dts
            "dts".to_string(),
            "-o".to_string(), // Output file name: system.dtb
            "system.dtb".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
