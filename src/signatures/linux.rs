use crate::signatures;

pub const LINUX_BOOT_IMAGE_DESCRIPTION: &str = "Linux kernel boot image";
pub const LINUX_KERNEL_VERSION_DESCRIPTION: &str = "Linux kernel version";

pub fn linux_boot_image_magic() -> Vec<Vec<u8>> {
    return vec![b"\xb8\xc0\x07\x8e\xd8\xb8\x00\x90\x8e\xc0\xb9\x00\x01\x29\xf6\x29".to_vec()];
}

pub fn linux_kernel_version_magic() -> Vec<Vec<u8>> {
    return vec![b"Linux\x20version\x20".to_vec()];
}

pub fn linux_boot_image_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // There should be the string "!HdrS" 514 bytes from the start of the magic signature
    const HDRS_OFFSET: usize = 514;
    const HDRS_EXPECTED_VALUE: &str = "!HdrS";

    let result = signatures::common::SignatureResult {
                                            description: LINUX_BOOT_IMAGE_DESCRIPTION.to_string(),
                                            offset: offset,
                                            size: 0,
                                            ..Default::default()
    };

    // Sanity check the size of available data
    if file_data.len() >= (offset + HDRS_OFFSET + HDRS_EXPECTED_VALUE.len()) {
        // Calculate start and end offset of the expected !HdrS string
        let hdrs_start: usize = offset + HDRS_OFFSET;
        let hdrs_end: usize = hdrs_start + HDRS_EXPECTED_VALUE.len();

        // Get the string that should equal HDRS_EXPECTED_VALUE
        if let Ok(actual_hdrs_value) = String::from_utf8(file_data[hdrs_start..hdrs_end].to_vec()) {
            // Validate that the hdrs string matches
            if actual_hdrs_value == HDRS_EXPECTED_VALUE {
                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}

pub fn linux_kernel_version_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // Kernel version string format is expected to be something like: "2.6.36"
    const KERNEL_VERSION_STRING_START: usize= 14;
    const KERNEL_VERSION_STRING_END: usize = 20;
    const PERIOD: u8 = 0x2E;
    const PERIOD_OFFSET_1: usize = 1;
    const PERIOD_OFFSET_2: usize = 3;

    let mut result = signatures::common::SignatureResult {
                                            description: LINUX_KERNEL_VERSION_DESCRIPTION.to_string(),
                                            offset: offset,
                                            size: 0,
                                            ..Default::default()
    };

    // Sanity check the size of available data
    if file_data.len() >= (offset + KERNEL_VERSION_STRING_END) {
        // Pull out the raw bytes that should be the Linux kernel version string
        let kernel_version_string_bytes = file_data[offset+KERNEL_VERSION_STRING_START..offset+KERNEL_VERSION_STRING_END].to_vec();

        // Convert the version string bytes into a string and do some sanity checking
        if let Ok(kernel_version_string) = String::from_utf8(kernel_version_string_bytes.clone()) {
            if kernel_version_string_bytes[PERIOD_OFFSET_1] == PERIOD && kernel_version_string_bytes[PERIOD_OFFSET_2] == PERIOD {
                result.description = format!("{} {}", result.description, kernel_version_string);
                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
