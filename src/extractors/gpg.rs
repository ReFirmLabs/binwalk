use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::inflate;

/// Defines the internal extractor function for decompressing signed GPG data
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::gpg::gpg_extractor;
///
/// match gpg_extractor().utility {
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
pub fn gpg_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(gpg_decompress),
        ..Default::default()
    }
}

/// Internal extractor for decompressing signed GPG data
pub fn gpg_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // Size of the GPG header
    const HEADER_SIZE: usize = 2;

    let mut exresult = ExtractionResult {
        ..Default::default()
    };

    // Do the decompression, ignoring the GPG header
    let inflate_result =
        inflate::inflate_decompressor(file_data, offset + HEADER_SIZE, output_directory);

    // Check that the data decompressed OK
    if inflate_result.success {
        exresult.success = true;
        exresult.size = Some(HEADER_SIZE + inflate_result.size);
    }

    exresult
}
