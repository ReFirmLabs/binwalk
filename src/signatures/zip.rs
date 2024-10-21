use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::zip::{parse_eocd_header, parse_zip_header};
use aho_corasick::AhoCorasick;

/// Human readable description
pub const DESCRIPTION: &str = "ZIP archive";

/// ZIP file entry magic bytes
pub fn zip_magic() -> Vec<Vec<u8>> {
    vec![b"PK\x03\x04".to_vec()]
}

/// Validates a ZIP file entry signature
pub fn zip_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Parse the ZIP file header
    if parse_zip_header(&file_data[offset..]).is_ok() {
        // Locate the end-of-central-directory header, which must come after the zip local file entries
        if let Ok(zip_info) = find_zip_eof(file_data, offset) {
            result.size = zip_info.eof - offset;
            result.description = format!(
                "{}, file count: {}, total size: {} bytes",
                result.description, zip_info.file_count, result.size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}

struct ZipEOCDInfo {
    eof: usize,
    file_count: usize,
}

/// Need to grep the rest of the file data to locate the end-of-central-directory header, which tells us where the ZIP file ends.
fn find_zip_eof(file_data: &[u8], offset: usize) -> Result<ZipEOCDInfo, SignatureError> {
    // This magic string assumes that the disk_number and central_directory_disk_number are 0
    const ZIP_EOCD_MAGIC: &[u8; 8] = b"PK\x05\x06\x00\x00\x00\x00";

    // Instatiate AhoCorasick search with the ZIP EOCD magic bytes
    let grep = AhoCorasick::new(vec![ZIP_EOCD_MAGIC]).unwrap();

    // Find all matching ZIP EOCD patterns
    for eocd_match in grep.find_overlapping_iter(&file_data[offset..]) {
        // Calculate the start and end of the fixed-size portion of the ZIP EOCD header in the file data
        let eocd_start: usize = eocd_match.start() + offset;

        // Parse the end-of-central-directory header
        if let Some(eocd_data) = file_data.get(eocd_start..) {
            if let Ok(eocd_header) = parse_eocd_header(eocd_data) {
                return Ok(ZipEOCDInfo {
                    eof: eocd_start + eocd_header.size,
                    file_count: eocd_header.file_count,
                });
            }
        }
    }

    // No valid EOCD record found :(
    Err(SignatureError)
}
