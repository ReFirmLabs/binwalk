use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::inflate;

/// Size of the checksum that follows the ZLIB deflate data stream
pub const CHECKSUM_SIZE: usize = 4;

/// Defines the internal extractor function for decompressing zlib data
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::zlib::zlib_extractor;
///
/// match zlib_extractor().utility {
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
pub fn zlib_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(zlib_decompress),
        ..Default::default()
    }
}

/// Internal extractor for decompressing ZLIB data
pub fn zlib_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Size of the zlib header
    const HEADER_SIZE: usize = 2;

    // Do the decompression, ignoring the ZLIB header
    let mut result =
        inflate::inflate_decompressor(file_data, offset + HEADER_SIZE, output_directory);

    // If the decompression reported the size of the deflate data, update the reported size
    // to include the ZLIB header and checksum fields
    if let Some(deflate_size) = result.size {
        result.size = Some(HEADER_SIZE + deflate_size + CHECKSUM_SIZE);
    }

    result
}
