use crate::signatures;
use crate::structures::rar::parse_rar_archive_header;
use aho_corasick::AhoCorasick;
use std::collections::HashMap;

pub const DESCRIPTION: &str = "RAR archive";

pub fn rar_magic() -> Vec<Vec<u8>> {
    return vec![b"Rar!\x1A\x07".to_vec()];
}

pub fn rar_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    let mut extra_description: String = "".to_string();

    // Parse the archive header
    if let Ok(rar_header) = parse_rar_archive_header(&file_data[offset..]) {
        // Try to locate the RAR end-of-file marker
        if let Ok(rar_size) = get_rar_size(&file_data[offset..], rar_header.version) {
            result.size = rar_size;
            result.confidence = signatures::common::CONFIDENCE_MEDIUM;
        } else {
            extra_description = " (failed to locate RAR EOF)".to_string();
        }

        result.description = format!(
            "{}, version: {}, total size: {} bytes{}",
            result.description, rar_header.version, result.size, extra_description
        );
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}

fn get_rar_size(
    file_data: &[u8],
    rar_version: usize,
) -> Result<usize, signatures::common::SignatureError> {
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
        for eof_match in grep.find_overlapping_iter(file_data) {
            // Accept the first match; total size is the start of the EOF marker plus the size of the EOF marker
            return Ok(eof_match.start() + eof_marker[0].len());
        }
    }

    return Err(signatures::common::SignatureError);
}
