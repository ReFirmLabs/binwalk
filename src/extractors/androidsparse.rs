use crate::structures::androidsparse;
use crate::extractors::common::{ Extractor, ExtractorType, ExtractionResult, safe_path_join, append_to_file };

// Defines the internal extractor function for decompressing zlib data
pub fn android_sparse_extractor() -> Extractor {
    return Extractor { utility: ExtractorType::Internal(extract_android_sparse), ..Default::default() };
}

pub fn extract_android_sparse(file_data: &Vec<u8>, offset: usize, output_directory: Option<&String>) -> ExtractionResult {
    const OUTFILE_NAME: &str = "unsparsed.img";

    let dry_run: bool;
    let outfile_path: String;
    let mut result = ExtractionResult { ..Default::default() };
        
    // Check if this is a dry-run or a full extraction
    match output_directory {
        Some(outdir) => {
            dry_run = false;
            outfile_path = safe_path_join(outdir, &OUTFILE_NAME.to_string());
        },
        None => {
            dry_run = true;
            outfile_path = "".to_string();
        },
    }

    // Parse the sparse file header
    if let Ok(sparse_header) = androidsparse::parse_android_sparse_header(&file_data[offset..]) {

        let mut processed_chunk_count: usize = 0;
        let mut next_chunk_offset: usize = offset + sparse_header.header_size;

        // Sanity check the size of available data before processing the next chunk
        while next_chunk_offset < file_data.len() {

            // Parse the next chunk's header
            match androidsparse::parse_android_sparse_chunk_header(&file_data[next_chunk_offset..]) {
                Err(_) => {
                    break;
                },

                Ok(chunk_header) => {
                    // Sanity check the reported size of the next chunk's data
                    if file_data.len() < (next_chunk_offset + chunk_header.header_size + chunk_header.data_size) {
                        break;
                    }

                    // If not a dry run, extract the data from the next chunk
                    if dry_run == false {

                        let chunk_data_start: usize = next_chunk_offset + chunk_header.header_size;
                        let chunk_data_end: usize = chunk_data_start + chunk_header.data_size;

                        if extract_chunk(&sparse_header, &chunk_header, &file_data[chunk_data_start..chunk_data_end], &outfile_path) == false {
                            break;
                        }
                    }

                    processed_chunk_count += 1;
                    next_chunk_offset += chunk_header.header_size + chunk_header.data_size;
                },
            }
        }

        // Make sure the number of processed chunks equals the number of chunks reported in the sparse flie header
        if processed_chunk_count == sparse_header.chunk_count {
            result.success = true;
            result.size = Some(next_chunk_offset - offset);
        }
    }

    return result;
}

// Extract a sparse file chunk to disk
fn extract_chunk(sparse_header: &androidsparse::AndroidSparseHeader, chunk_header: &androidsparse::AndroidSparseChunkHeader, chunk_data: &[u8], outfile_path: &String) -> bool {

    if chunk_header.is_raw == true {

        // Raw chunks are just data chunks stored verbatim
        if append_to_file(outfile_path, chunk_data) == false {
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
            if append_to_file(outfile_path, &fill_block) == false {
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
            if append_to_file(outfile_path, &null_block) == false {
                return false;
            }
        }
    }

    return true;
}
