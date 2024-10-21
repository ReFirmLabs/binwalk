use crate::common::epoch_to_string;
use crate::extractors::uimage::extract_uimage;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::uimage::parse_uimage_header;

/// Human readable description
pub const DESCRIPTION: &str = "uImage firmware image";

/// uImage magic bytes
pub fn uimage_magic() -> Vec<Vec<u8>> {
    vec![b"\x27\x05\x19\x56".to_vec()]
}

/// Validates uImage signatures
pub fn uimage_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        size: 0,
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    // Do an extraction dry-run
    let dry_run = extract_uimage(file_data, offset, None);

    if dry_run.success {
        if let Some(uimage_size) = dry_run.size {
            // Extraction dry-run ok, parse the header to display some useful info
            if let Ok(uimage_header) = parse_uimage_header(&file_data[offset..]) {
                // Configure SignatureResult; decline extraction if data size is 0 (looking at you, DD-WRT)
                result.size = uimage_size;
                result.extraction_declined = uimage_header.data_size == 0;
                result.description = format!("{}, header size: {} bytes, data size: {} bytes, compression: {}, CPU: {}, OS: {}, image type: {}, load address: {:#X}, entry point: {:#X}, creation time: {}, image name: \"{}\"",
                                                                                                                                    result.description,
                                                                                                                                    uimage_header.header_size,
                                                                                                                                    uimage_header.data_size,
                                                                                                                                    uimage_header.compression_type,
                                                                                                                                    uimage_header.cpu_type,
                                                                                                                                    uimage_header.os_type,
                                                                                                                                    uimage_header.image_type,
                                                                                                                                    uimage_header.load_address,
                                                                                                                                    uimage_header.entry_point_address,
                                                                                                                                    epoch_to_string(uimage_header.timestamp as u32),
                                                                                                                                    uimage_header.name);

                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
