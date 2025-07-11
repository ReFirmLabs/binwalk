use crate::signatures::common::{CONFIDENCE_MEDIUM, SignatureError, SignatureResult};
use crate::structures::qcow::parse_qcow_header;

pub const DESCRIPTION: &str = "QEMU QCOW Image";

pub fn qcow_magic() -> Vec<Vec<u8>> {
    vec![b"QFI\xFB".to_vec()]
}

pub fn qcow_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        name: "qcow".to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(qcow_header) = parse_qcow_header(file_data) {
        result.description = format!(
            "QEMU QCOW Image, version: {}, storage media size: {:#x} bytes, cluster block size: {:#x} bytes, encryption method: {}",
            qcow_header.version,
            qcow_header.storage_media_size,
            1 << qcow_header.cluster_block_bits,
            qcow_header.encryption_method
        );
        return Ok(result);
    };

    Err(SignatureError)
}
