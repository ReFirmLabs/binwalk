use crate::common::epoch_to_string;
use crate::extractors::uimage::extract_uimage;
use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use crate::structures::uimage::parse_uimage_header;

/// Human readable description
pub const DESCRIPTION: &str = "uImage firmware image";

/// uImage magic bytes
pub fn uimage_magic() -> Vec<Vec<u8>> {
    vec![
        // Standard uImage magic
        b"\x27\x05\x19\x56".to_vec(),
        // Alternate uImage magic (https://git.openwrt.org/?p=openwrt/openwrt.git;a=commitdiff;h=01a1e21863aa30c7a2c252ff06b9aef0cf957970)
        b"OKLI".to_vec(),
    ]
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
                result.size = uimage_size;
                // Decline extraction if the header CRC does not match, or if the reported data size is 0
                result.extraction_declined =
                    !uimage_header.header_crc_valid || uimage_header.data_size == 0;
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
                // If the header CRC is invalid, adjust the reported confidence level and report the checksum mis-match
                if !uimage_header.header_crc_valid {
                    // If the uImage header was otherwise valid and starts at file offset 0 then we're still fairly confident in the result
                    if result.offset == 0 {
                        result.confidence = CONFIDENCE_MEDIUM;
                    } else {
                        result.confidence = CONFIDENCE_LOW;
                    }

                    result.description = format!("{}, invalid checksum", result.description);
                }

                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
