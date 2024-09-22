use crate::extractors;

/* Describes how to run the 7z utility to extract DMG images. This kinda-sorta works, sometimes. DMG is a bitch. */
pub fn dmg_extractor() -> extractors::common::Extractor {
    return extractors::common::Extractor {
                        utility: extractors::common::ExtractorType::External("7z".to_string()),
                        extension: "dmg".to_string(),
                        arguments: vec![
                                        "x".to_string(), // Perform extraction
                                        "-y".to_string(), // Assume Yes to all questions
                                        "-o.".to_string(), // Output to current working directory
                                        extractors::common::SOURCE_FILE_PLACEHOLDER.to_string()
                        ],
                        // If there is trailing data after the compressed data, extraction will happen but exit code will be 2
                        exit_codes: vec![0, 2],
                        ..Default::default()
    };
}
