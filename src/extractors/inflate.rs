use crate::extractors::common::{Chroot, ExtractionResult};
use miniz_oxide::inflate;

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
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const MIN_DECOMPRESSED_SIZE: usize = 1;
    const DECOMPRESS_TEST_SIZE: usize = 512;
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";

    let dry_run: bool;
    let compressed_data_start: usize = offset;
    let mut compressed_data_end: usize = file_data.len();

    let mut result = ExtractionResult {
        ..Default::default()
    };

    match output_directory {
        None => {
            dry_run = true;
        }
        Some(_) => {
            dry_run = false;
        }
    }

    // During a dry run, limit the size of compressed data to DECOMPRESS_TEST_SIZE.
    if dry_run == true && compressed_data_end > (compressed_data_start + DECOMPRESS_TEST_SIZE) {
        compressed_data_end = compressed_data_start + DECOMPRESS_TEST_SIZE;
    }

    // Do decompression
    // WARNING: The decompressed data is stored completely in memory. Use flate2 wrapper instead?
    match inflate::decompress_to_vec(&file_data[compressed_data_start..compressed_data_end]) {
        Ok(decompressed_data) => {
            // Make sure some data was actually decompresed
            if decompressed_data.len() > 0 {
                if dry_run == true {
                    result.success = true;
                } else {
                    let chroot = Chroot::new(output_directory);
                    result.success = chroot.create_file(OUTPUT_FILE_NAME, &decompressed_data);
                }
            }
        }
        Err(e) => {
            /*
             * Failure due to truncated data is possible, and expected, when doing a dry run since
             * the compressed data provided to the inflate function is truncated to DECOMPRESS_TEST_SIZE bytes.
             * In this case, consider decompression a success.
             */
            if dry_run == true
                && e.status == inflate::TINFLStatus::FailedCannotMakeProgress
                && e.output.len() >= MIN_DECOMPRESSED_SIZE
            {
                result.success = true;
            }
        }
    }

    return result;
}
