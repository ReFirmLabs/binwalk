use crate::extractors;

/// Describes how to run the dmg2img utility to convert DMG images to MBR
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::dmg::dmg_extractor;
///
/// match dmg_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
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
