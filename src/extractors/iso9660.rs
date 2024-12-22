use crate::extractors;
use crate::extractors::sevenzip::sevenzip_extractor;

/// Describes how to run the 7z utility to extract ISO images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::iso9660::iso9660_extractor;
///
/// match iso9660_extractor().utility {
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
pub fn iso9660_extractor() -> extractors::common::Extractor {
    // Same as the normal 7z extractor, but give the carved file an ISO file extension.
    // The file extension matters, and 7z doesn't handle some ISO sub-formats correctly if the file extension is not '.iso'.
    let mut extractor = sevenzip_extractor();
    extractor.extension = "iso".to_string();
    extractor
}
