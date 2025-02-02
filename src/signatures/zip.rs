use crate::common::is_offset_safe;
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
    if let Ok(zip_file_header) = parse_zip_header(&file_data[offset..]) {
        // Locate the end-of-central-directory header, which must come after the zip local file entries
        match find_zip_eof(file_data, offset) {
            Ok(zip_info) => {
                result.size = zip_info.eof - offset;
                result.description = format!(
                    "{}, version: {}.{}, file count: {}, total size: {} bytes",
                    result.description,
                    zip_file_header.version_major,
                    zip_file_header.version_minor,
                    zip_info.file_count,
                    result.size
                );
            }
            // If the ZIP file is corrupted and no EOCD header exists, attempt to parse all the individual ZIP file headers
            Err(_) => {
                let available_data = file_data.len() - offset;
                let mut previous_file_header_offset = None;
                let mut next_file_header_offset = offset + zip_file_header.total_size;

                while is_offset_safe(
                    available_data,
                    next_file_header_offset,
                    previous_file_header_offset,
                ) {
                    match parse_zip_header(&file_data[next_file_header_offset..]) {
                        Ok(zip_header) => {
                            previous_file_header_offset = Some(next_file_header_offset);
                            next_file_header_offset += zip_header.total_size;
                        }
                        Err(_) => {
                            result.size = next_file_header_offset - offset;
                            result.description = format!(
                                "{}, version: {}.{}, missing end-of-central-directory header, total size: {} bytes",
                                result.description,
                                zip_file_header.version_major,
                                zip_file_header.version_minor,
                                result.size
                            );
                            break;
                        }
                    }
                }
            }
        }

        // Only return success if the identified ZIP file is larger than the first ZIP file entry
        if result.size > zip_file_header.total_size {
            return Ok(result);
        }
    }

    Err(SignatureError)
}

pub struct ZipEOCDInfo {
    pub eof: usize,
    pub file_count: usize,
}

/// Need to grep the rest of the file data to locate the end-of-central-directory header, which tells us where the ZIP file ends.
pub fn find_zip_eof(file_data: &[u8], offset: usize) -> Result<ZipEOCDInfo, SignatureError> {
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
