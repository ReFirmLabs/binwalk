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
    output_directory: Option<&str>,
) -> ExtractionResult {
    // Size of the zlib header
    const HEADER_SIZE: usize = 2;

    let mut exresult = ExtractionResult {
        ..Default::default()
    };

    // Do the decompression, ignoring the ZLIB header
    let inflate_result =
        inflate::inflate_decompressor(file_data, offset + HEADER_SIZE, output_directory);

    // Check that the data decompressed OK
    if inflate_result.success {
        // Calculate the ZLIB checksum offsets
        let checksum_start = offset + HEADER_SIZE + inflate_result.size;
        let checksum_end = checksum_start + CHECKSUM_SIZE;

        // Get the ZLIB checksum
        if let Some(adler32_checksum_bytes) = file_data.get(checksum_start..checksum_end) {
            let reported_checksum = u32::from_be_bytes(adler32_checksum_bytes.try_into().unwrap());

            // Make sure the checksum matches
            if reported_checksum == inflate_result.adler32 {
                exresult.success = true;
                exresult.size = Some(HEADER_SIZE + inflate_result.size + CHECKSUM_SIZE);
            }
        }
    }

    exresult
}
