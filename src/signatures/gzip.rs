use crate::common;
use crate::extractors::gzip::gzip_decompress;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::gzip::parse_gzip_header;

/// Human readable description
pub const DESCRIPTION: &str = "gzip compressed data";

/// Gzip magic bytes, plus compression type field (always 8 for deflate)
pub fn gzip_magic() -> Vec<Vec<u8>> {
    return vec![b"\x1f\x8b\x08".to_vec()];
}

/// Validates gzip signatures
pub fn gzip_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
    // Do a dry-run decompression
    let dry_run = gzip_decompress(file_data, offset, None);

    // If dry-run was successful, this is almost certianly a valid gzip file
    if dry_run.success == true {
        // The dry run has already validated the header, but we want some header info to display to the user
        if let Ok(gzip_header) = parse_gzip_header(&file_data[offset..]) {
            // Original file name is optional
            let mut original_file_name_text: String = "".to_string();

            if gzip_header.original_name.len() > 0 {
                original_file_name_text =
                    format!(" original file name: \"{}\",", gzip_header.original_name);
            }

            return Ok(SignatureResult {
                offset: offset,
                confidence: CONFIDENCE_HIGH,
                description: format!(
                    "{},{} operating system: {}, timestamp: {}",
                    DESCRIPTION,
                    original_file_name_text,
                    gzip_header.os,
                    common::epoch_to_string(gzip_header.timestamp)
                ),
                ..Default::default()
            });
        }
    }

    return Err(SignatureError);
}
