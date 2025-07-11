use crate::common::is_offset_safe;
use crate::extractors::lzma::lzma_decompress;
use crate::extractors::sevenzip::sevenzip_extractor;
use crate::signatures::common::{CONFIDENCE_HIGH, SignatureError, SignatureResult};
use crate::structures::xz::parse_xz_header;

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
    let mut stream_header_count = 0;
    let available_data = file_data.len() - offset;

    // XZ streams can be concatenated together, need to process them all to determine the size of an XZ file
    while is_offset_safe(available_data, next_offset, previous_offset) {
        // Parse the next XZ header to validate the header CRC
        match parse_xz_header(&file_data[next_offset..]) {
            Err(_) => break,
            Ok(_) => {
                // Header is valid
                stream_header_count += 1;

                // Do an extraction dry-run to make sure the data decompresses correctly
                let dry_run = lzma_decompress(file_data, next_offset, None);

                // If dry run was a success, update the offset and size fields
                if dry_run.success && dry_run.size.is_some() {
                    previous_offset = Some(next_offset);
                    next_offset += dry_run.size.unwrap();
                    result.size += dry_run.size.unwrap();
                // Else, report that the data is malformed and stop processing XZ streams
                } else {
                    // 7z may be able to at least partially extract malformed data streams
                    result.preferred_extractor = Some(sevenzip_extractor());
                    result.description = format!(
                        "{}, valid header with malformed data stream",
                        result.description
                    );
                    break;
                }
            }
        }
    }

    // Return success if at least one valid XZ stream header was found
    if stream_header_count > 0 {
        // Only report the total size if we were able to determine the total size
        if result.size > 0 {
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
        }
        return Ok(result);
    }

    Err(SignatureError)
}
