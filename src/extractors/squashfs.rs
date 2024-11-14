use crate::extractors;

/// Describes how to run the sasquatch utility to extract SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_extractor;
///
/// match squashfs_extractor().utility {
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

/// Describes how to run the sasquatch utility to extract little endian SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_le_extractor;
///
/// match squashfs_le_extractor().utility {
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
pub fn squashfs_le_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("sasquatch".to_string()),
        extension: "sqsh".to_string(),
        arguments: vec![
            "-le".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // Exit code may be 0 or 2; 2 indicates running as not root, but otherwise extraction is ok
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the sasquatch utility to extract big endian SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_be_extractor;
///
/// match squashfs_be_extractor().utility {
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
pub fn squashfs_be_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External("sasquatch".to_string()),
        extension: "sqsh".to_string(),
        arguments: vec![
            "-be".to_string(),
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
        ],
        // Exit code may be 0 or 2; 2 indicates running as not root, but otherwise extraction is ok
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the sasquatch-v4be utility to extract big endian SquashFSv4 images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_v4_be_extractor;
///
/// match squashfs_v4_be_extractor().utility {
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
