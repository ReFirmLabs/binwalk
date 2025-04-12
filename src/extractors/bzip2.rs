use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use bzip2::{Decompress, Status};

/// Defines the internal extractor function for decompressing BZIP2 files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::bzip2::bzip2_extractor;
///
/// match bzip2_extractor().utility {
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
pub fn bzip2_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(bzip2_decompressor),
        ..Default::default()
    }
}

/// Internal extractor for decompressing BZIP2 data
pub fn bzip2_decompressor(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // Size of decompression buffer
    const BLOCK_SIZE: usize = 900 * 1024;
    // Output file for decompressed data
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    let mut bytes_written: usize = 0;
    let mut stream_offset: usize = 0;
    let bzip2_data = &file_data[offset..];
    let mut decompressed_buffer = [0; BLOCK_SIZE];
    let mut decompressor = Decompress::new(false);
    let available_data = bzip2_data.len();
    let mut previous_offset = None;

    /*
     * Loop through all compressed data and decompress it.
     *
     * This has a significant performance hit since 1) decompression takes time, and 2) data is
     * decompressed once during signature validation and a second time during extraction (if extraction
     * was requested).
     *
     * The advantage is that not only are we 100% sure that this data is valid BZIP2 data, but we
     * can also determine the exact size of the BZIP2 data.
     */
    while is_offset_safe(available_data, stream_offset, previous_offset) {
        previous_offset = Some(stream_offset);

        // Decompress a block of data
        match decompressor.decompress(&bzip2_data[stream_offset..], &mut decompressed_buffer) {
            Err(_) => {
                // Break on decompression error
                break;
            }
            Ok(status) => {
                match status {
                    Status::RunOk => break,
                    Status::FlushOk => break,
                    Status::FinishOk => break,
                    Status::MemNeeded => break,
                    Status::Ok => {
                        stream_offset = decompressor.total_in() as usize;
                    }
                    Status::StreamEnd => {
                        result.success = true;
                        result.size = Some(decompressor.total_in() as usize);
                    }
                }

                // Decompressed a block of data, if extraction was requested write the decompressed block to the output file
                if output_directory.is_some() {
                    let n: usize = (decompressor.total_out() as usize) - bytes_written;

                    let chroot = Chroot::new(output_directory);
                    if !chroot.append_to_file(OUTPUT_FILE_NAME, &decompressed_buffer[0..n]) {
                        // If writing data to file fails, break
                        break;
                    }

                    bytes_written += n;
                }

                // If everything has been processed successfully, we're done; break.
                if result.success {
                    break;
                }
            }
        }
    }

    result
}
