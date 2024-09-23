use crate::signatures;
use crate::structures::iso9660::parse_iso_header;

pub const DESCRIPTION: &str = "ISO9660 primary volume";

pub fn iso_magic() -> Vec<Vec<u8>> {
    return vec![b"\x01CD001\x01\x00".to_vec()];
}

pub fn iso_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // Offset from the beginning of the ISO image to the magic bytes
    const ISO_MAGIC_OFFSET: usize = 32768;

    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    // We need at least ISO_MAGIC_OFFSET bytes to exist before the magic match offset
    if offset >= ISO_MAGIC_OFFSET {
        // Calculate the actual starting offset of the ISO
        result.offset = offset - ISO_MAGIC_OFFSET;

        if let Ok(iso_header) = parse_iso_header(&file_data[result.offset..]) {
            result.size = iso_header.image_size;
            result.description =
                format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
