use crate::extractors::common::{Chroot, ExtractionResult};
use flate2::bufread::DeflateDecoder;
use std::io::Read;

/*
 * The inflate_decompressor extractor is currently not directly used by any signature definitions.
 *
use crate::extractors::common::{ Extractor, ExtractorType };

// Defines the internal extractor function for decompressing raw deflate data
pub fn inflate_extractor() -> Extractor {
    return Extractor { utility: ExtractorType::Internal(inflate_decompressor), ..Default::default() };
}
*/

/// Internal extractor for inflating deflated data.
pub fn inflate_decompressor(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Size of decompression buffer
    const BLOCK_SIZE: usize = 8192;
    // Output file for decompressed data
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    let mut decompressed_buffer = [0; BLOCK_SIZE];
    let mut decompressor = DeflateDecoder::new(&file_data[offset..]);

    /*
     * Loop through all compressed data and decompress it.
     *
     * This has a significant performance hit since 1) decompression takes time, and 2) data is
     * decompressed once during signature validation and a second time during extraction (if extraction
     * was requested).
     *
     * The advantage is that not only are we 100% sure that this data is a valid deflate stream, but we
     * can also determine the exact size of the deflated data.
     */
    loop {
        // Decompress a block of data
        match decompressor.read(&mut decompressed_buffer) {
            Err(_) => {
                // Break on decompression error
                break;
            }
            Ok(n) => {
                // Decompressed a block of data, if extraction was requested write the decompressed block to the output file
                if n > 0 && output_directory.is_some() {
                    let chroot = Chroot::new(output_directory);
                    if !chroot.append_to_file(OUTPUT_FILE_NAME, &decompressed_buffer[0..n]) {
                        // If writing data to file fails, break
                        break;
                    }
                }

                // No data was read, end of compression stream
                if n == 0 {
                    // If some data was actually decompressed, report success and the number of input bytes consumed
                    if decompressor.total_out() > 0 {
                        result.success = true;
                        result.size = Some(decompressor.total_in() as usize);
                    }

                    // Nothing else to do, break
                    break;
                }
            }
        }
    }

    result
}
