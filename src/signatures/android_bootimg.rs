use crate::signatures::common::{
    SignatureError, SignatureResult, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
};
use crate::structures::android_bootimg::parse_android_bootimg_header;

/// Human readable description
pub const DESCRIPTION: &str = "Android boot image";

/// Android boot images always start with these bytes
pub fn android_bootimg_magic() -> Vec<Vec<u8>> {
    vec![b"ANDROID!".to_vec()]
}

/// Validates the android boot image header
pub fn android_bootimg_parser(
    file_data: &[u8],
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_LOW,
        ..Default::default()
    };

    if let Ok(bootimg_header) = parse_android_bootimg_header(&file_data[offset..]) {
        if offset == 0 {
            result.confidence = CONFIDENCE_MEDIUM;
        }

        result.description = format!(
            "{}, kernel size: {} bytes, kernel load address: {:#X}, ramdisk size: {} bytes, ramdisk load address: {:#X}",
            result.description,
            bootimg_header.kernel_size,
            bootimg_header.kernel_load_address,
            bootimg_header.ramdisk_size,
            bootimg_header.ramdisk_load_address,
        );
        return Ok(result);
    }

    Err(SignatureError)
}
