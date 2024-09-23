use crate::signatures;
use crate::structures::xz::{parse_xz_footer, parse_xz_header};
use aho_corasick::AhoCorasick;

pub const DESCRIPTION: &str = "XZ compressed data";

pub fn xz_magic() -> Vec<Vec<u8>> {
    return vec![b"\xFD\x37\x7a\x58\x5a\x00".to_vec()];
}

pub fn xz_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Ok(header_size) = parse_xz_header(&file_data[offset..]) {
        if let Ok(stream_size) = xz_stream_size(&file_data[offset + header_size..]) {
            // Total size is the header size plus the data stream size
            result.size = header_size + stream_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    };

    return Err(signatures::common::SignatureError);
}

/*
 * XZ file format has detectable, verifiable, end-of-stream markers.
 */
fn xz_stream_size(xz_data: &[u8]) -> Result<usize, signatures::common::SignatureError> {
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
        let footer_start = match_offset - FOOTER_MAGIC_OFFSET;

        // Need at least FOOTER_MAGIC_OFFSET bytes before the magic match
        if match_offset >= FOOTER_MAGIC_OFFSET {
            // Footer must be 4-byte aligned
            if (footer_start % 4) == 0 {
                // Parse the stream footer
                if let Ok(footer_size) = parse_xz_footer(&xz_data[footer_start..]) {
                    return Ok(footer_start + footer_size);
                }
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
