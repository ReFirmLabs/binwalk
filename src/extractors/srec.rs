use crate::extractors;

/// Describes how to run the srec2bin utility to convert Motorola S-records to binary
pub fn srec_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("srec2bin".to_string()),
        extension: "hex".to_string(),
        arguments: vec![
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            "s-record.bin".to_string(),
        ],
        exit_codes: vec![0],
        ..Default::default()
    }
}
