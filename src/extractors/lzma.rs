use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use lzma;

// Defines the internal extractor function for decompressing gzip data
pub fn lzma_extractor() -> Extractor {
    return Extractor {
        utility: ExtractorType::Internal(lzma_decompress),
        ..Default::default()
    };
}

pub fn lzma_decompress(
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const TEST_BUF_SIZE: usize = 1024;
    const DATA_TRUNCATED_ERR_STR: &str = "Buf";
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";

    let dry_run: bool;
    let lzma_data_size: usize;
    let available_data: usize = file_data.len() - offset;
    let mut result = ExtractionResult {
        ..Default::default()
    };

    match output_directory {
        None => {
            dry_run = true;
            lzma_data_size = TEST_BUF_SIZE;
        }
        Some(_) => {
            dry_run = false;
            lzma_data_size = available_data;
        }
    }

    if available_data >= lzma_data_size {
        // Do decompression, check error status, if data is truncated, type will be 'Buf'
        match lzma::decompress(&file_data[offset..offset + lzma_data_size]) {
            Ok(decompressed_data) => {
                if dry_run == false {
                    let chroot = Chroot::new(output_directory);
                    result.success =
                        chroot.create_file(OUTPUT_FILE_NAME, &decompressed_data);
                } else {
                    result.success = true;
                }
            }
            Err(e) => {
                if let lzma::error::LzmaError::Io(ref io_error) = e {
                    if let Some(lzma_error) = io_error.get_ref() {
                        let type_str = format!("{:?}", lzma_error);
                        // Truncation error is only considered successful during dry runs
                        if type_str == DATA_TRUNCATED_ERR_STR && dry_run == true {
                            result.success = true;
                        }
                    }
                }
            }
        }
    }

    return result;
}
