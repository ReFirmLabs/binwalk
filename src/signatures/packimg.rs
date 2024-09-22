use crate::signatures;
use crate::structures::packimg::parse_packimg_header;

pub const DESCRIPTION: &str = "PackImg firmware header";

pub fn packimg_magic() -> Vec<Vec<u8>> {
    return vec![b"--PaCkImGs--".to_vec()];
}

pub fn packimg_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    
    let mut result = signatures::common::SignatureResult {
                                            size: 0,
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    if let Ok(packimg_header) = parse_packimg_header(&file_data[offset..]) {

        // Sanity check the reported data size
        if available_data >= (packimg_header.header_size + packimg_header.data_size) {
            result.size = packimg_header.header_size;
            result.description = format!("{}, header size: {} bytes, data size: {} bytes", result.description,
                                                                                           packimg_header.header_size,
                                                                                           packimg_header.data_size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
