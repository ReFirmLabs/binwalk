use crate::signatures;
use crate::structures::chk::parse_chk_header;

pub const DESCRIPTION: &str = "CHK firmware header";

pub fn chk_magic() -> Vec<Vec<u8>> {
    return vec![b"\x2A\x23\x24\x5E".to_vec()];
}

pub fn chk_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    if let Ok(chk_header) = parse_chk_header(&file_data[offset..]) {

        let available_data: usize = file_data.len() - offset;
        let image_total_size: usize = chk_header.header_size + chk_header.kernel_size + chk_header.rootfs_size;

        // Total reported image size should be between the header size and the file size
        if available_data >= image_total_size && image_total_size > chk_header.header_size {
            // Report the size of the header and a brief description
            result.size = chk_header.header_size;
            result.description = format!("{}, board ID: {}, header size: {} bytes, data size: {} bytes", result.description,
                                                                                                         chk_header.board_id,
                                                                                                         chk_header.header_size,
                                                                                                         chk_header.kernel_size + chk_header.rootfs_size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
