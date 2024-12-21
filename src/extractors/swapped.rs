use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};

/// Defines the internal extractor function for u16 swapped firmware images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::swapped::swapped_extractor_u16;
///
/// match swapped_extractor_u16().utility {
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
pub fn swapped_extractor_u16() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_swapped_u16),
        ..Default::default()
    }
}

/// Extract firmware where every two bytes have been swapped
pub fn extract_swapped_u16(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const SWAP_BYTE_COUNT: usize = 2;
    extract_swapped(file_data, offset, output_directory, SWAP_BYTE_COUNT)
}

/// Extract a block of data where every n bytes have been swapped
fn extract_swapped(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
    n: usize,
) -> ExtractionResult {
    const OUTPUT_FILE_NAME: &str = "swapped.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    if let Some(data) = file_data.get(offset..) {
        let swapped_data = byte_swap(data, n);

        result.success = !swapped_data.is_empty();

        if result.success {
            result.size = Some(swapped_data.len());

            // Write to file, if requested
            if output_directory.is_some() {
                let chroot = Chroot::new(output_directory);
                result.success = chroot.create_file(OUTPUT_FILE_NAME, &swapped_data);
            }
        }
    }

    result
}

/// Swap every n bytes of the provided data
///
/// ## Example:
///
/// ```
/// use binwalk::extractors::swapped::byte_swap;
///
/// assert_eq!(byte_swap(b"ABCD", 2), b"CDAB");
/// ```
pub fn byte_swap(data: &[u8], n: usize) -> Vec<u8> {
    let chunk_size = n * 2;
    let mut chunker = data.chunks(chunk_size);
    let mut swapped_data: Vec<u8> = Vec::new();

    loop {
        match chunker.next() {
            None => {
                break;
            }
            Some(chunk) => {
                if chunk.len() != chunk_size {
                    break;
                }

                swapped_data.extend(chunk[n..].to_vec());
                swapped_data.extend(chunk[0..n].to_vec());
            }
        }
    }

    swapped_data
}
