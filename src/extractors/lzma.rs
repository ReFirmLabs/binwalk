use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use xz2::stream::{Action, Status, Stream};

/// Defines the internal extractor function for decompressing LZMA/XZ data
pub fn lzma_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(lzma_decompress),
        ..Default::default()
    }
}

/// Internal extractor for decompressing LZMA/XZ data streams
pub fn lzma_decompress(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Output file name
    const OUTPUT_FILE_NAME: &str = "decompressed.bin";
    // Output buffer size
    const BLOCK_SIZE: usize = 8192;
    // Maximum memory limit: 4GB
    const MEM_LIMIT: u64 = 4 * 1024 * 1024 * 1024;

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Output buffer
    let mut output_buf = [0; BLOCK_SIZE];

    // Input compression stream
    let lzma_stream = &file_data[offset..];

    // Instantiate a new decoder, auto-detect LZMA or XZ
    if let Ok(mut decompressor) = Stream::new_auto_decoder(MEM_LIMIT, 0) {
        // Tracks number of bytes written to disk
        let mut bytes_written: usize = 0;
        // Tracks current position of bytes consumed from input stream
        let mut stream_position: usize = 0;

        /*
         * Loop through all compressed data and decompress it.
         *
         * This has a significant performance hit since 1) decompression takes time, and 2) data is
         * decompressed once during signature validation and a second time during extraction (if extraction
         * was requested).
         *
         * The advantage is that not only are we 100% sure that this data is a valid LZMA stream, but we
         * can also determine the exact size of the LZMA data.
         */
        loop {
            // Decompress data into output_buf
            match decompressor.process(
                &lzma_stream[stream_position..],
                &mut output_buf,
                Action::Run,
            ) {
                Err(_) => {
                    // Decompression error, break
                    break;
                }
                Ok(status) => {
                    // Check reported status
                    match status {
                        Status::GetCheck => break,
                        Status::MemNeeded => break,
                        Status::Ok => {
                            // Decompression OK, but there is still more data to decompress
                            stream_position = decompressor.total_in() as usize;
                        }
                        Status::StreamEnd => {
                            // Decompression complete. If some data was decompressed, report success, else break.
                            if decompressor.total_out() > 0 {
                                result.success = true;
                                result.size = Some(decompressor.total_in() as usize);
                            } else {
                                break;
                            }
                        }
                    }

                    // Some data was decompressed successfully; if extraction was requested, write the data to disk.
                    if output_directory.is_some() {
                        // Number of decompressed bytes in the output buffer
                        let n = (decompressor.total_out() as usize) - bytes_written;

                        let chroot = Chroot::new(output_directory);
                        if !chroot.append_to_file(OUTPUT_FILE_NAME, &output_buf[0..n]) {
                            // If writing data to disk fails, report failure and break
                            result.success = false;
                            break;
                        }

                        // Remember how much data has been written to disk
                        bytes_written += n;
                    }

                    // If result.success is true, then everything has been processed and written to disk successfully.
                    if result.success {
                        break;
                    }
                }
            }
        }
    }

    result
}
