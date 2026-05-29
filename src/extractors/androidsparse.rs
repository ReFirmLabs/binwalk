use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::androidsparse;

/// Defines the internal extractor function for extracting Android Sparse files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::androidsparse::android_sparse_extractor;
///
/// match android_sparse_extractor().utility {
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
    output_directory: Option<&str>,
) -> ExtractionResult {
    const OUTFILE_NAME: &str = "unsparsed.img";

    // Refuse to produce an unsparsed image larger than this. Real-world Android
    // partitions are well under this cap; anything beyond is almost certainly a
    // crafted header trying to exhaust disk space.
    const MAX_UNSPARSED_SIZE: usize = 16 * 1024 * 1024 * 1024; // 16 GiB

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the sparse file header
    if let Ok(sparse_header) = androidsparse::parse_android_sparse_header(&file_data[offset..]) {
        // Sanity check the declared total output size. checked_mul guards against
        // u32 * u32 overflowing usize, and the comparison guards against absurd
        // but non-overflowing values (e.g., 256 TB).
        match sparse_header
            .block_count
            .checked_mul(sparse_header.block_size)
        {
            Some(s) if s <= MAX_UNSPARSED_SIZE => {}
            _ => return result,
        };

        let available_data: usize = file_data.len();
        let mut last_chunk_offset: Option<usize> = None;
        let mut processed_chunk_count: usize = 0;
        let mut blocks_written: usize = 0;
        let mut next_chunk_offset: usize = offset + sparse_header.header_size;

        while is_offset_safe(available_data, next_chunk_offset, last_chunk_offset) {
            // Parse the next chunk's header
            match androidsparse::parse_android_sparse_chunk_header(&file_data[next_chunk_offset..])
            {
                Err(_) => {
                    break;
                }

                Ok(chunk_header) => {
                    // A single chunk can never describe more blocks than the
                    // total declared by the sparse header. This bounds the
                    // cumulative output to max_output_size.
                    blocks_written = match blocks_written.checked_add(chunk_header.block_count) {
                        Some(n) if n <= sparse_header.block_count => n,
                        _ => break,
                    };

                    // For RAW chunks the payload must exactly cover block_count
                    // blocks; otherwise the extracted image would be silently
                    // misaligned and an absurd block_count would still drive
                    // unbounded reads via file_data.get().
                    if chunk_header.is_raw {
                        let expected = chunk_header
                            .block_count
                            .checked_mul(sparse_header.block_size);
                        if expected != Some(chunk_header.data_size) {
                            break;
                        }
                    }

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
                                OUTFILE_NAME,
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
    outfile: &str,
    chroot: &Chroot,
) -> bool {
    if chunk_header.is_raw {
        // Raw chunks are just data chunks stored verbatim
        if !chroot.append_to_file(outfile, chunk_data) {
            return false;
        }
    } else if chunk_header.is_fill {
        // The parser rejects FILL chunks whose payload isn't the spec-required
        // 4 bytes, but guard here too: an empty fill value would make the inner
        // loop below spin forever.
        if chunk_data.is_empty() {
            return false;
        }
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
