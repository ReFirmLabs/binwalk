use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::uefi::{parse_uefi_capsule_header, parse_uefi_volume_header};

/// Human readable descriptions
pub const VOLUME_DESCRIPTION: &str = "UEFI PI firmware volume";
pub const CAPSULE_DESCRIPTION: &str = "UEFI capsule image";

/// UEFI volume magic bytes
pub fn uefi_volume_magic() -> Vec<Vec<u8>> {
    vec![b"_FVH".to_vec()]
}

/// UEFI capsule GUIDs
pub fn uefi_capsule_magic() -> Vec<Vec<u8>> {
    vec![
        b"\xBD\x86\x66\x3B\x76\x0D\x30\x40\xB7\x0E\xB5\x51\x9E\x2F\xC5\xA0".to_vec(), // EFI capsule GUID
        b"\x8B\xA6\x3C\x4A\x23\x77\xFB\x48\x80\x3D\x57\x8C\xC1\xFE\xC4\x4D".to_vec(), // EFI2 capsule GUID
        b"\xB9\x82\x91\x53\xB5\xAB\x91\x43\xB6\x9A\xE3\xA9\x43\xF7\x2F\xCC".to_vec(), // UEFI capsule GUID
    ]
}

/// Validates UEFI volume signatures
pub fn uefi_volume_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // The magic signature begins this many bytes from the start of the UEFI volume
    const UEFI_MAGIC_OFFSET: usize = 40;

    let mut result = SignatureResult {
        size: 0,
        offset: 0,
        description: VOLUME_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    // Volume actually starts UEFI_MAGIC_OFFSET bytes before the magic bytes; make sure there are at least that many bytes preceeding the magic offset
    if offset >= UEFI_MAGIC_OFFSET {
        // Set the correct starting offset for this volume
        result.offset = offset - UEFI_MAGIC_OFFSET;

        // Parse the volume header
        if let Ok(uefi_volume_header) = parse_uefi_volume_header(&file_data[result.offset..]) {
            // Make sure the volume size is sane
            if file_data.len() >= (result.offset + uefi_volume_header.volume_size) {
                result.size = uefi_volume_header.volume_size;
                result.description = format!(
                    "{}, header CRC: {:#X}, header size: {} bytes, total size: {} bytes",
                    result.description,
                    uefi_volume_header.header_crc as u32,
                    uefi_volume_header.header_size,
                    uefi_volume_header.volume_size
                );
                return Ok(result);
            }
        }
    }

    Err(SignatureError)
}

/// Validates UEFI capsule signatures
pub fn uefi_capsule_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Success return value
    let mut result = SignatureResult {
        description: CAPSULE_DESCRIPTION.to_string(),
        offset,
        size: 0,
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    if let Ok(capsule_header) = parse_uefi_capsule_header(&file_data[offset..]) {
        // Sanity check on header total size field
        if capsule_header.total_size >= available_data {
            result.size = capsule_header.total_size;
            result.description = format!(
                "{}, header size: {} bytes, total size: {} bytes",
                result.description, capsule_header.header_size, capsule_header.total_size
            );
            return Ok(result);
        }
    }

    Err(SignatureError)
}
