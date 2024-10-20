use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::androidsparse;

/// Defines the internal extractor function for decompressing zlib data
pub fn android_sparse_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_android_sparse),
        ..Default::default()
    }
}

/// Android sparse internal extractor
pub fn extract_android_sparse(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "unsparsed.img";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the sparse file header
    if let Ok(sparse_header) = androidsparse::parse_android_sparse_header(&file_data[offset..]) {
        let available_data: usize = file_data.len();
        let mut last_chunk_offset: Option<usize> = None;
        let mut processed_chunk_count: usize = 0;
        let mut next_chunk_offset: usize = offset + sparse_header.header_size;

        while is_offset_safe(available_data, next_chunk_offset, last_chunk_offset) {
            // Parse the next chunk's header
            match androidsparse::parse_android_sparse_chunk_header(&file_data[next_chunk_offset..])
            {
                Err(_) => {
                    break;
                }

                Ok(chunk_header) => {
                    // If not a dry run, extract the data from the next chunk
                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);
                        let chunk_data_start: usize = next_chunk_offset + chunk_header.header_size;
                        let chunk_data_end: usize = chunk_data_start + chunk_header.data_size;

                        if let Some(chunk_data) = file_data.get(chunk_data_start..chunk_data_end) {
                            if !extract_chunk(
                                &sparse_header,
                                &chunk_header,
                                chunk_data,
                                &OUTFILE_NAME.to_string(),
                                &chroot,
                            ) {
                                break;
                            }
                        } else {
                            break;
                        }
                    }

                    processed_chunk_count += 1;
                    last_chunk_offset = Some(next_chunk_offset);
                    next_chunk_offset += chunk_header.header_size + chunk_header.data_size;
                }
            }
        }

        // Make sure the number of processed chunks equals the number of chunks reported in the sparse flie header
        if processed_chunk_count == sparse_header.chunk_count {
            result.success = true;
            result.size = Some(next_chunk_offset - offset);
        }
    }

    result
}

// Extract a sparse file chunk to disk
fn extract_chunk(
    sparse_header: &androidsparse::AndroidSparseHeader,
    chunk_header: &androidsparse::AndroidSparseChunkHeader,
    chunk_data: &[u8],
    outfile: &String,
    chroot: &Chroot,
) -> bool {
    if chunk_header.is_raw {
        // Raw chunks are just data chunks stored verbatim
        if !chroot.append_to_file(outfile, chunk_data) {
            return false;
        }
    } else if chunk_header.is_fill {
        // Fill chunks are block_count blocks that contain a repeated sequence of data (typically 4-bytes repeated over and over again)
        for _ in 0..chunk_header.block_count {
            let mut i = 0;
            let mut fill_block: Vec<u8> = vec![];

            // Fill each block with the repeated data
            while i < sparse_header.block_size {
                fill_block.extend(chunk_data);
                i += chunk_data.len();
            }

            // Append fill block to file
            if !chroot.append_to_file(outfile, &fill_block) {
                return false;
            }
        }
    } else if chunk_header.is_dont_care {
        let mut null_block: Vec<u8> = vec![];

        // Build a block full of NULL bytes
        while null_block.len() < sparse_header.block_size {
            null_block.push(0);
        }

        // Write block_count NULL blocks to disk
        for _ in 0..chunk_header.block_count {
            if !chroot.append_to_file(outfile, &null_block) {
                return false;
            }
        }
    }

    true
}
