use crate::common::is_offset_safe;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::xz::{parse_xz_footer, parse_xz_header};
use aho_corasick::AhoCorasick;

/// Human readable description
pub const DESCRIPTION: &str = "XZ compressed data";

/// XZ magic bytes
pub fn xz_magic() -> Vec<Vec<u8>> {
    vec![b"\xFD\x37\x7a\x58\x5a\x00".to_vec()]
}

/// Validates XZ signatures
pub fn xz_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let mut next_offset = offset;
    let mut previous_offset = None;
    let available_data = file_data.len() - offset;

    // XZ streams can be concatenated together, need to process them all to determine the size of an XZ file
    while is_offset_safe(available_data, next_offset, previous_offset) {
        // Parse the next XZ header to get the header's size
        match parse_xz_header(&file_data[next_offset..]) {
            Err(_) => break,
            Ok(header_size) => {
                match file_data.get(next_offset + header_size..) {
                    None => break,
                    Some(xz_stream_data) => {
                        // Determine the size of the XZ stream data
                        match xz_stream_size(xz_stream_data) {
                            Err(_) => break,
                            Ok(stream_size) => {
                                previous_offset = Some(next_offset);
                                next_offset += header_size + stream_size;
                            }
                        }
                    }
                }
            }
        }
    }

    // If at least one valid header and one valid stream were identified,
    // next_offset will be greater than the starting offset.
    if next_offset > offset {
        result.size = next_offset - offset;
        result.description = format!("{}, total size: {} bytes", result.description, result.size);
        return Ok(result);
    }

    Err(SignatureError)
}

/// XZ file format has detectable, verifiable, end-of-stream markers.
fn xz_stream_size(xz_data: &[u8]) -> Result<usize, SignatureError> {
    // The magic bytes we search for ("YZ") are actually 10 bytes into the footer header
    const FOOTER_MAGIC_OFFSET: usize = 10;

    /*
     * Gotta grep for the end-of-stream magic bytes ("YZ").
     * These are prone to false positives, but a valid footer includes a checksum,
     * making false positive matches easy to filter out (see: parse_xz_footer).
     */
    let eof_pattern = vec![b"YZ"];
    let grep = AhoCorasick::new(eof_pattern).unwrap();

    // Find all matching patterns in the xz compressed data
    for eof_match in grep.find_overlapping_iter(xz_data) {
        let match_offset: usize = eof_match.start();
        let footer_start: usize = match_offset - FOOTER_MAGIC_OFFSET;

        // Footer must be 4-byte aligned
        if (footer_start % 4) == 0 {
            if let Some(footer_data) = xz_data.get(footer_start..) {
                // Parse the stream footer
                if let Ok(footer_size) = parse_xz_footer(footer_data) {
                    return Ok(footer_start + footer_size);
                }
            }
        }
    }

    Err(SignatureError)
}
