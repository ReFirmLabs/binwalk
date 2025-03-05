use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use crate::structures::arj::parse_arj_header;

pub const DESCRIPTION: &str = "ARJ archive data";
pub fn arj_magic() -> Vec<Vec<u8>> {
    vec![b"\x60\xea".to_vec()]
}

pub fn arj_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    if let Ok(arj_header) = parse_arj_header(&file_data[offset..]) {
        let available_data = file_data.len() - offset;
        // Sanity check the reported ARJ header size
        if arj_header.header_size <= available_data {
            // Return success
            return Ok(SignatureResult {
                description: format!(
                    "{}, header size: {}, version {}, minimum version to extract: {}, flags: {}, compression method: {}, file type: {}, original name: {}, original file date: {}, compressed file size: {}, uncompressed file size: {}, os: {}",
                    DESCRIPTION,
                    arj_header.header_size,
                    arj_header.version,
                    arj_header.min_version,
                    arj_header.flags,
                    arj_header.compression_method,
                    arj_header.file_type,
                    arj_header.original_name,
                    arj_header.original_file_date,
                    arj_header.compressed_file_size,
                    arj_header.uncompressed_file_size,
                    arj_header.host_os,
                ),
                offset,
                size: arj_header.header_size,
                confidence: CONFIDENCE_MEDIUM,
                extraction_declined: arj_header.file_type != *"comment header",
                ..Default::default()
            });
        }
    }

    Err(SignatureError)
}
