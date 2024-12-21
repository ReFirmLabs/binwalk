use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::extractors::inflate;
use crate::structures::gzip::parse_gzip_header;

/// Defines the internal extractor function for decompressing gzip data
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::gzip::gzip_extractor;
///
/// match gzip_extractor().utility {
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
pub fn gzip_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(gzip_decompress),
        ..Default::default()
    }
}

/// Internal extractor for gzip compressed data
pub fn gzip_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    let mut exresult = ExtractionResult {
        ..Default::default()
    };

    // Parse the gzip header
    if let Ok(gzip_header) = parse_gzip_header(&file_data[offset..]) {
        // Deflate compressed data starts at the end of the gzip header
        let deflate_data_start: usize = offset + gzip_header.size;

        if file_data.len() > deflate_data_start {
            let inflate_result =
                inflate::inflate_decompressor(file_data, deflate_data_start, output_directory);
            if inflate_result.success {
                exresult.success = true;
                exresult.size = Some(inflate_result.size);
            }
        }
    }

    exresult
}
