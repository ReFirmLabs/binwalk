use crate::structures;

pub const CPIO_HEADER_SIZE: usize = 110;

#[derive(Debug, Clone, Default)]
pub struct CPIOEntryHeader {
    pub magic: Vec<u8>,
    pub data_size: usize,
    pub file_name: String,
    pub header_size: usize,
}

// TODO: If file mode parsing is added, internal extractor would be pretty easy to implement...
pub fn parse_cpio_entry_header(
    cpio_data: &[u8],
) -> Result<CPIOEntryHeader, structures::common::StructureError> {
    const NULL_BYTE_SIZE: usize = 1;
    const CPIO_MAGIC_START: usize = 0;
    const CPIO_MAGIC_END: usize = 6;
    const FILE_SIZE_START: usize = 54;
    const FILE_SIZE_END: usize = 62;
    const FILE_NAME_SIZE_START: usize = 94;
    const FILE_NAME_SIZE_END: usize = 102;

    let available_data: usize = cpio_data.len();

    if available_data > CPIO_HEADER_SIZE {
        // Grab the CPIO header magic bytes
        let header_magic = cpio_data[CPIO_MAGIC_START..CPIO_MAGIC_END].to_vec();

        // Get the ASCII hex string representing the file's data size
        if let Ok(file_data_size_str) =
            String::from_utf8(cpio_data[FILE_SIZE_START..FILE_SIZE_END].to_vec())
        {
            // Convert the file data size from ASCII hex to an integer
            if let Ok(file_data_size) = usize::from_str_radix(&file_data_size_str, 16) {
                // Get the ASCII hex string representing the file name's size
                if let Ok(file_name_size_str) =
                    String::from_utf8(cpio_data[FILE_NAME_SIZE_START..FILE_NAME_SIZE_END].to_vec())
                {
                    // Convert the file name size from ASCII hex to an integer
                    if let Ok(file_name_size) = usize::from_str_radix(&file_name_size_str, 16) {
                        // The file name immediately follows the fixed-length header data.
                        let file_name_start: usize = CPIO_HEADER_SIZE;
                        let file_name_end: usize =
                            file_name_start + file_name_size - NULL_BYTE_SIZE;

                        if let Some(file_name_raw_bytes) = cpio_data.get(file_name_start..file_name_end) {
                            if let Ok(file_name) = String::from_utf8(file_name_raw_bytes.to_vec()) {
                                let header_total_size = CPIO_HEADER_SIZE + file_name_size;

                                return Ok(CPIOEntryHeader {
                                    magic: header_magic.clone(),
                                    file_name: file_name.clone(),
                                    data_size: file_data_size + byte_padding(file_data_size),
                                    header_size: header_total_size
                                        + byte_padding(header_total_size),
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}

// File data and CPIO headers are padded to 4-byte boundaries
fn byte_padding(n: usize) -> usize {
    let modulus: usize = n % 4;
    if modulus == 0 {
        return 0;
    } else {
        return 4 - modulus;
    }
}
