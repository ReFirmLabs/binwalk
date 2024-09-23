use crate::common::crc32;
use crate::signatures;
use crate::structures::sevenzip::parse_7z_header;

pub const DESCRIPTION: &str = "7-zip archive data";

pub fn sevenzip_magic() -> Vec<Vec<u8>> {
    return vec![b"7z\xbc\xaf\x27\x1c".to_vec()];
}

pub fn sevenzip_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    if let Ok(sevenzip_header) = parse_7z_header(&file_data[offset..]) {
        // Calculate the start and end offsets that the next header CRC was calculated over
        let next_crc_start: usize =
            offset + sevenzip_header.header_size + sevenzip_header.next_header_offset;
        let next_crc_end: usize = next_crc_start + sevenzip_header.next_header_size;

        // Sanity check the offsets of the next_header fields
        if next_crc_end <= file_data.len() {
            // Calculate the next_header CRC
            let calculated_next_crc: usize =
                crc32(&file_data[next_crc_start..next_crc_end]) as usize;

            // Validate the next_header CRC
            if calculated_next_crc == sevenzip_header.next_header_crc {
                // Calculate total size of the 7zip archive
                let total_size: usize = sevenzip_header.header_size
                    + sevenzip_header.next_header_offset
                    + sevenzip_header.next_header_size;

                // Report signature result
                return Ok(signatures::common::SignatureResult {
                    offset: offset,
                    size: total_size,
                    confidence: signatures::common::CONFIDENCE_HIGH,
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

    return Err(signatures::common::SignatureError);
}
