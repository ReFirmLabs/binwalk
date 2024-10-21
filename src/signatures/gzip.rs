use crate::common;
use crate::extractors::gzip::gzip_decompress;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::gzip::parse_gzip_header;

/// Human readable description
pub const DESCRIPTION: &str = "gzip compressed data";

/// Gzip magic bytes, plus compression type field (always 8 for deflate)
pub fn gzip_magic() -> Vec<Vec<u8>> {
    vec![b"\x1f\x8b\x08".to_vec()]
}

/// Validates gzip signatures
pub fn gzip_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Length of the GZIP CRC located at the end of the deflate data stream
    const GZIP_CRC_SIZE: usize = 4;
    // Length of the ISIZE field located after the CRC field
    const GZIP_ISIZE_SIZE: usize = 4;

    // Do a dry-run decompression
    let dry_run = gzip_decompress(file_data, offset, None);

    // If dry-run was successful, this is almost certianly a valid gzip file
    if dry_run.success {
        // Get the size of the deflate data stream
        if let Some(deflate_data_size) = dry_run.size {
            // The dry run has already validated the header, but we want some header info to display to the user
            if let Ok(gzip_header) = parse_gzip_header(&file_data[offset..]) {
                // Original file name is optional
                let mut original_file_name_text: String = "".to_string();

                if !gzip_header.original_name.is_empty() {
                    original_file_name_text =
                        format!(" original file name: \"{}\",", gzip_header.original_name);
                }

                // Total size of the gzip file is the size of the header, plus the size of the compressed data, plus the trailing CRC and ISIZE fields
                let total_size =
                    gzip_header.size + deflate_data_size + GZIP_CRC_SIZE + GZIP_ISIZE_SIZE;

                return Ok(SignatureResult {
                    offset,
                    size: total_size,
                    confidence: CONFIDENCE_HIGH,
                    description: format!(
                        "{},{} operating system: {}, timestamp: {}, total size: {} bytes",
                        DESCRIPTION,
                        original_file_name_text,
                        gzip_header.os,
                        common::epoch_to_string(gzip_header.timestamp),
                        total_size,
                    ),
                    ..Default::default()
                });
            }
        }
    }

    Err(SignatureError)
}
