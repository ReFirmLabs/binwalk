use crate::common::epoch_to_string;
use crate::signatures;
use crate::structures::uimage::parse_uimage_header;

pub const DESCRIPTION: &str = "uImage firmware header";

pub fn uimage_magic() -> Vec<Vec<u8>> {
    return vec![b"\x27\x05\x19\x56".to_vec()];
}

pub fn uimage_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    if let Ok(uimage_header) = parse_uimage_header(&file_data[offset..]) {
        result.size = uimage_header.header_size;
        result.description = format!("{}, header size: {} bytes, data size: {} bytes, compression: {}, CPU: {}, OS: {}, image type: {}, creation time: {}, image name: \"{}\"",
                                                                                                                            result.description,
                                                                                                                            uimage_header.header_size,
                                                                                                                            uimage_header.data_size,
                                                                                                                            uimage_header.compression_type,
                                                                                                                            uimage_header.cpu_type,
                                                                                                                            uimage_header.os_type,
                                                                                                                            uimage_header.image_type,
                                                                                                                            epoch_to_string(uimage_header.timestamp as u32),
                                                                                                                            uimage_header.name);

        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
