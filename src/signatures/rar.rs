use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::rar::parse_rar_archive_header;
use aho_corasick::AhoCorasick;
use std::collections::HashMap;

/// Human readable description
pub const DESCRIPTION: &str = "RAR archive";

/// RAR magic bytes for both v4 and v5
pub fn rar_magic() -> Vec<Vec<u8>> {
    vec![b"Rar!\x1A\x07".to_vec()]
}

/// Validate RAR signature
pub fn rar_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let mut extra_description: String = "".to_string();

    // Parse the archive header
    if let Ok(rar_header) = parse_rar_archive_header(&file_data[offset..]) {
        // Try to locate the RAR end-of-file marker
        if let Ok(rar_size) = get_rar_size(&file_data[offset..], rar_header.version) {
            result.size = rar_size;
            result.confidence = CONFIDENCE_MEDIUM;
        } else {
            extra_description = " (failed to locate RAR EOF)".to_string();
        }

        result.description = format!(
            "{}, version: {}, total size: {} bytes{}",
            result.description, rar_header.version, result.size, extra_description
        );
        return Ok(result);
    }

    Err(SignatureError)
}

/// Determine the size of the RAR file
fn get_rar_size(file_data: &[u8], rar_version: usize) -> Result<usize, SignatureError> {
    // EOF markers for Rar v4 and v5
    let eof_markers: HashMap<usize, Vec<Vec<u8>>> = HashMap::from([
        (4, vec![b"\xC4\x3D\x7B\x00\x40\x07\x00".to_vec()]),
        (5, vec![b"\x1d\x77\x56\x51\x03\x05\x04\x00".to_vec()]),
    ]);

    if eof_markers.contains_key(&rar_version) {
        // Select the appropriate EOF marker for this version
        let eof_marker = &eof_markers[&rar_version];

        // Need to grep the file for the EOF marker
        let grep = AhoCorasick::new(eof_marker.clone()).unwrap();

        // Search the file data for the EOF marker
        if let Some(eof_match) = grep.find_overlapping_iter(file_data).next() {
            // Accept the first match; total size is the start of the EOF marker plus the size of the EOF marker
            return Ok(eof_match.start() + eof_marker[0].len());
        }
    }

    Err(SignatureError)
}
