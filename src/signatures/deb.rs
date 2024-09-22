use crate::signatures;
use crate::structures::deb::parse_deb_header;

pub const DESCRIPTION: &str = "Debian package file";

pub fn deb_magic() -> Vec<Vec<u8>> {
    return vec![b"!<arch>\ndebian-binary\x20\x20\x20".to_vec()];
}

pub fn deb_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
                                            size: 0,
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };

    if let Ok(deb_header) = parse_deb_header(&file_data[offset..]) {
        result.size = deb_header.file_size;

        // Make sure the reported size of the DEB file is sane
        if result.size <= (file_data.len() - offset) {
            result.description = format!("{}, total size: {} bytes", result.description, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
