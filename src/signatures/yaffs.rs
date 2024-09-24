use crate::signatures;
use crate::structures::yaffs::{parse_yaffs_file_header, parse_yaffs_obj_header};

const MIN_NUMBER_OF_OBJS: usize = 2;

pub const DESCRIPTION: &str = "YAFFS filesystem";

pub fn yaffs_magic() -> Vec<Vec<u8>> {
    // Expect the first YAFFS entry to be either a directory (0x00000003) or file (0x00000001), big or little endian
    return vec![
        b"\x03\x00\x00\x00\x01\x00\x00\x00\xFF\xFF".to_vec(),
        b"\x00\x00\x00\x03\x00\x00\x00\x01\xFF\xFF".to_vec(),
        b"\x01\x00\x00\x00\x01\x00\x00\x00\xFF\xFF".to_vec(),
        b"\x00\x00\x00\x01\x00\x00\x00\x01\xFF\xFF".to_vec(),
    ];
}

pub fn yaffs_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const MAX_OBJ_SIZE: usize = 16896;
    const BIG_ENDIAN_FIRST_BYTE: u8 = 0;

    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        offset: offset,
        size: 0,
        confidence: signatures::common::CONFIDENCE_HIGH,
        ..Default::default()
    };

    let mut endianness = "little";

    // Sanity check the amount of available data
    if file_data.len() >= (MAX_OBJ_SIZE * MIN_NUMBER_OF_OBJS) {
        // Detect endianness
        if file_data[offset] == BIG_ENDIAN_FIRST_BYTE {
            endianness = "big";
        }

        let page_size = get_page_size(&file_data[offset..]);
        let spare_size = get_spare_size(&file_data[offset..], page_size, endianness);

        if let Ok(image_size) =
            get_image_size(&file_data[offset..], page_size, spare_size, endianness)
        {
            result.size = image_size;
            result.description = format!(
                "{}, {} endian, page size: {}, spare size: {}, image size: {} bytes",
                result.description, endianness, page_size, spare_size, image_size
            );
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}

// Returns the detected page size used by the YAFFS image
fn get_page_size(file_data: &[u8]) -> usize {
    // Spare data must be at least this big
    const MIN_PAGE_SIZE: usize = 16;

    // Index in page_sizes of the YAFFS1 page size
    const YAFFS1_PAGE_SIZE_INDEX: usize = 0;

    // Spare area is expected to start with these bytes, depending on endianess and ECC settings (YAFFS2 only)
    let spare_magics: Vec<Vec<u8>> = vec![
        b"\x00\x00\x10\x00".to_vec(),
        b"\x00\x10\x00\x00".to_vec(),
        b"\xFF\xFF\x00\x00\x10\x00".to_vec(),
        b"\xFF\xFF\x00\x10\x00\x00".to_vec(),
    ];

    // Valid YAFFS page sizes
    let page_sizes: Vec<usize> = vec![512, 1024, 2048, 4096, 8192, 16384];

    // Loop through each page size looking for one that is immediately followed by a valid spare data entry.
    // This is only for YAFFS2! It will fail for YAFFS1 images, but YAFFS1 uses a fixed page size anyway.
    for page_size in &page_sizes {
        // Make sure there is enough data to hold a page and spare block
        if (page_size + MIN_PAGE_SIZE) < file_data.len() {
            // Loop through all the expected start of spare data signatures
            for spare_magic in &spare_magics {
                let start_spare_offset: usize = *page_size;
                let end_spare_offset: usize = start_spare_offset + spare_magic.len();

                // If this spare data starts with the expected bytes, then we've guessed the page size correctly
                if file_data[start_spare_offset..end_spare_offset] == *spare_magic {
                    return *page_size;
                }
            }
        }
    }

    // Nothing found, try the YAFFS1 page size
    return page_sizes[YAFFS1_PAGE_SIZE_INDEX];
}

// Returns the detected spare size of the YAFFS image
fn get_spare_size(file_data: &[u8], page_size: usize, endianness: &str) -> usize {
    // Index in spare_sizes of the YAFFS1 spare size
    const YAFFS1_SPARE_SIZE_INDEX: usize = 0;

    let spare_sizes: Vec<usize> = vec![16, 32, 64, 128, 256, 512];

    // Loop through all spare sizes until a valid object header is found
    for spare_size in &spare_sizes {
        // If this spare size is correct, this should be the location of the next object header
        let next_obj_offset: usize = (page_size + *spare_size) * MIN_NUMBER_OF_OBJS;

        // Sanity check available file data
        if next_obj_offset < file_data.len() {
            // Attempt to parse this data as a YAFFS object header
            if let Ok(_) = parse_yaffs_obj_header(&file_data[next_obj_offset..], endianness) {
                return *spare_size;
            }
        }
    }

    // Nothing found, try the YAFFS1 page size
    return spare_sizes[YAFFS1_SPARE_SIZE_INDEX];
}

// Returns the total size of the image, in bytes
fn get_image_size(
    file_data: &[u8],
    page_size: usize,
    spare_size: usize,
    endianness: &str,
) -> Result<usize, signatures::common::SignatureError> {
    const FILE_TYPE: usize = 1;

    let mut image_size: usize = 0;
    let block_size: usize = page_size + spare_size;

    // Loop through all available data, parsing YAFFS object headers
    while (image_size + block_size) <= file_data.len() {
        // Get the necessary data to process this object entry
        let obj_start: usize = image_size;
        let obj_end: usize = obj_start + block_size;
        let obj_data = &file_data[obj_start..obj_end];

        // Parse and validate the object header
        match parse_yaffs_obj_header(&obj_data, endianness) {
            Err(_e) => break,
            Ok(header) => {
                // Each object header takes up at least one block of data
                let mut data_blocks: usize = 1;

                // If this is a file, the file data wil take up additional data blocks
                if header.obj_type == FILE_TYPE {
                    match get_file_block_count(&obj_data, page_size, endianness) {
                        Err(e) => {
                            return Err(e);
                        }
                        Ok(block_count) => {
                            data_blocks += block_count;
                        }
                    }
                }

                // Calculate the total distance until the next object header
                let next_obj_offset: usize = data_blocks * block_size;

                // Sanity check the reported offset
                if (image_size + next_obj_offset) <= file_data.len() {
                    image_size += next_obj_offset;
                } else {
                    break;
                }
            }
        }
    }

    // Sanity check the calculated image size
    if image_size > (block_size * MIN_NUMBER_OF_OBJS) && image_size <= file_data.len() {
        return Ok(image_size);
    }

    return Err(signatures::common::SignatureError);
}

// Returns the number of data blocks used to store file data; this size is only valid for file type objects
fn get_file_block_count(
    obj_data: &[u8],
    page_size: usize,
    endianness: &str,
) -> Result<usize, signatures::common::SignatureError> {
    // parse_yaffs_file_header only parses a portion of the header that we need; the partial structure starts this many bytes into the object data
    const INFO_STRUCT_START: usize = 268;

    // Parse the partial object header.
    if let Ok(file_info) = parse_yaffs_file_header(&obj_data[INFO_STRUCT_START..], endianness) {
        // File data is broken up into blocks of page_size bytes
        let file_block_count: usize =
            ((file_info.file_size as f64) / (page_size as f64)).ceil() as usize;
        return Ok(file_block_count);
    }

    return Err(signatures::common::SignatureError);
}
