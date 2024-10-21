use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::cab::parse_cab_header;

/// Human readable description
pub const DESCRIPTION: &str = "Microsoft Cabinet archive";

/// CAB magic bytes; includes the magic bytes and the following reserved1 header entry, which must be 0.
pub fn cab_magic() -> Vec<Vec<u8>> {
    vec![b"MSCF\x00\x00\x00\x00".to_vec()]
}

/// Parses and cabinet file signature
pub fn cab_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Parse the CAB header
    if let Ok(cab_header) = parse_cab_header(&file_data[offset..]) {
        let available_data = file_data.len() - offset;

        // Sanity check the reported CAB file size
        if cab_header.total_size <= available_data {
            // Return success
            return Ok(SignatureResult {
                description: format!(
                    "{}, file count: {}, folder count: {}, header size: {}, total size: {} bytes",
                    DESCRIPTION,
                    cab_header.file_count,
                    cab_header.folder_count,
                    cab_header.header_size,
                    cab_header.total_size
                ),
                offset,
                size: cab_header.total_size,
                confidence: CONFIDENCE_MEDIUM,
                ..Default::default()
            });
        }
    }

    Err(SignatureError)
}
