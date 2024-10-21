use crate::common::crc32;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::sevenzip::parse_7z_header;

/// Human readable description
pub const DESCRIPTION: &str = "7-zip archive data";

/// 7zip magic bytes
pub fn sevenzip_magic() -> Vec<Vec<u8>> {
    vec![b"7z\xbc\xaf\x27\x1c".to_vec()]
}

/// Validates 7zip signatures
pub fn sevenzip_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Parse the 7z header
    if let Ok(sevenzip_header) = parse_7z_header(&file_data[offset..]) {
        // Calculate the start and end offsets that the next header CRC was calculated over
        let next_crc_start: usize =
            offset + sevenzip_header.header_size + sevenzip_header.next_header_offset;
        let next_crc_end: usize = next_crc_start + sevenzip_header.next_header_size;

        if let Some(crc_data) = file_data.get(next_crc_start..next_crc_end) {
            // Calculate the next_header CRC
            let calculated_next_crc: usize = crc32(crc_data) as usize;

            // Validate the next_header CRC
            if calculated_next_crc == sevenzip_header.next_header_crc {
                // Calculate total size of the 7zip archive
                let total_size: usize = sevenzip_header.header_size
                    + sevenzip_header.next_header_offset
                    + sevenzip_header.next_header_size;

                // Report signature result
                return Ok(SignatureResult {
                    offset,
                    size: total_size,
                    confidence: CONFIDENCE_HIGH,
                    description: format!(
                        "{}, version {}.{}, total size: {} bytes",
                        DESCRIPTION,
                        sevenzip_header.major_version,
                        sevenzip_header.minor_version,
                        total_size
                    ),
                    ..Default::default()
                });
            }
        }
    }

    Err(SignatureError)
}
