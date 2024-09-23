use crate::signatures;
use crate::structures::zip::{parse_eocd_header, parse_zip_header};
use aho_corasick::AhoCorasick;

pub const DESCRIPTION: &str = "ZIP archive";

pub fn zip_magic() -> Vec<Vec<u8>> {
    return vec![b"PK\x03\x04".to_vec()];
}

pub fn zip_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Ok(_) = parse_zip_header(&file_data[offset..]) {
        // Locate the end-of-central-directory header, which must come after the zip local file entries
        if let Ok(zip_info) = find_zip_eof(&file_data, offset) {
            result.size = zip_info.eof - offset;
            result.description = format!(
                "{}, file count: {}, total size: {} bytes",
                result.description, zip_info.file_count, result.size
            );
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}

struct ZipEOCDInfo {
    eof: usize,
    file_count: usize,
}

/*
 * Need to grep the rest of the file data to locate the end-of-central-directory header, which tells us where the ZIP file ends.
 */
fn find_zip_eof(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<ZipEOCDInfo, signatures::common::SignatureError> {
    // This magic string assumes that the disk_number and central_directory_disk_number are 0 (see: zip_eocd_structure)
    const ZIP_EOCD_MAGIC: &[u8; 8] = b"PK\x05\x06\x00\x00\x00\x00";

    // Instatiate AhoCorasick search with the ZIP EOCD magic bytes
    let grep = AhoCorasick::new(vec![ZIP_EOCD_MAGIC]).unwrap();

    // Find all matching ZIP EOCD patterns
    for eocd_match in grep.find_overlapping_iter(&file_data[offset..]) {
        // Calculate the start and end of the fixed-size portion of the ZIP EOCD header in the file data
        let eocd_start: usize = eocd_match.start() + offset;

        if let Ok(eocd_header) = parse_eocd_header(&file_data[eocd_start..]) {
            return Ok(ZipEOCDInfo {
                eof: eocd_start + eocd_header.size,
                file_count: eocd_header.file_count,
            });
        }
    }

    // No valid EOCD record found :(
    return Err(signatures::common::SignatureError);
}
