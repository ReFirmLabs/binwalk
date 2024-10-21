use crate::extractors::jboot::extract_jboot_sch2_kernel;
use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_HIGH, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use crate::structures::jboot::{
    parse_jboot_arm_header, parse_jboot_sch2_header, parse_jboot_stag_header,
};

/// Human readable descriptions
pub const JBOOT_ARM_DESCRIPTION: &str = "JBOOT firmware header";
pub const JBOOT_STAG_DESCRIPTION: &str = "JBOOT STAG header";
pub const JBOOT_SCH2_DESCRIPTION: &str = "JBOOT SCH2 header";

/// JBOOT firmware header magic bytes
pub fn jboot_arm_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x42\x48\x02\x00\x00\x00"
            .to_vec(),
    ]
}

/// JBOOT STAG header magic bytes
pub fn jboot_stag_magic() -> Vec<Vec<u8>> {
    vec![b"\x04\x04\x24\x2B".to_vec(), b"\xFF\x04\x24\x2B".to_vec()]
}

/// JBOOT SCH2 header magic bytes
pub fn jboot_sch2_magic() -> Vec<Vec<u8>> {
    vec![
        b"\x24\x21\x00\x02".to_vec(),
        b"\x24\x21\x01\x02".to_vec(),
        b"\x24\x21\x02\x02".to_vec(),
        b"\x24\x21\x03\x02".to_vec(),
    ]
}

/// Parse and validate the JBOOT ARM header
pub fn jboot_arm_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Magic bytes start at this offset into the header
    const MAGIC_OFFSET: usize = 48;

    // Successful return value
    let mut result = SignatureResult {
        description: JBOOT_ARM_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Actual header starts MAGIC_OFFSET bytes before the magic bytes
    let header_start = offset - MAGIC_OFFSET;

    if let Some(jboot_data) = file_data.get(header_start..) {
        if let Ok(arm_header) = parse_jboot_arm_header(jboot_data) {
            result.size = arm_header.header_size;
            result.offset = header_start;
            result.description = format!("{}, header size: {} bytes, ROM ID: {}, erase offset: {:#X}, erase size: {:#X}, data flash offset: {:#X}, data size: {:#X}",
                result.description,
                arm_header.header_size,
                arm_header.rom_id,
                arm_header.erase_offset,
                arm_header.erase_size,
                arm_header.data_offset,
                arm_header.data_size,
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}

/// Parse and validate a JBOOT STAG header
pub fn jboot_stag_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: JBOOT_STAG_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(stag_header) = parse_jboot_stag_header(&file_data[offset..]) {
        // Sanity check on the stag header reported size; it is expected that this
        // type of header describes a kernel, and should not take up the entire firmware image
        if (offset + stag_header.header_size + stag_header.image_size) < file_data.len() {
            // Only report the header size, confidence in this signature is low, don't
            // want to skip a bunch of data on a false positive
            result.size = stag_header.header_size;

            let mut image_type: &str = "factory image";

            if stag_header.is_sysupgrade_image {
                image_type = "system upgrade image";
            }

            result.description = format!(
                "{}, {}, header size: {} bytes, kernel data size: {} bytes",
                result.description, image_type, stag_header.header_size, stag_header.image_size,
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}

/// Parse and validate a JBOOT SCH2 header
pub fn jboot_sch2_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: JBOOT_SCH2_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let dry_run = extract_jboot_sch2_kernel(file_data, offset, None);

    if dry_run.success {
        if let Some(total_size) = dry_run.size {
            if let Ok(sch2_header) = parse_jboot_sch2_header(&file_data[offset..]) {
                result.size = total_size;
                result.description = format!("{}, header size: {} bytes, kernel size: {} bytes, kernel compression: {}, kernel entry point: {:#X}",
                    result.description,
                    sch2_header.header_size,
                    sch2_header.kernel_size,
                    sch2_header.compression,
                    sch2_header.kernel_entry_point,
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}
