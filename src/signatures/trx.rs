use crate::signatures;
use crate::structures::trx::parse_trx_header;

pub const DESCRIPTION: &str = "TRX firmware header";

pub fn trx_magic() -> Vec<Vec<u8>> {
    return vec![b"HDR0".to_vec()];
}

pub fn trx_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_MEDIUM,
                                            ..Default::default()
    };

    if let Ok(trx_header) = parse_trx_header(&file_data[offset..]) {

        result.size = trx_header.header_size;
        result.description = format!("{}, version {}, header size: {} bytes, total size: {} bytes, bootloader offset: {:#X}, kernel offset: {:#X}, rootfs offset: {:#X}", result.description,
                                                                                                                                                                          trx_header.version,
                                                                                                                                                                          trx_header.header_size,
                                                                                                                                                                          trx_header.total_size,
                                                                                                                                                                          trx_header.boot_partition,
                                                                                                                                                                          trx_header.kernel_partition,
                                                                                                                                                                          trx_header.rootfs_partition);
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
