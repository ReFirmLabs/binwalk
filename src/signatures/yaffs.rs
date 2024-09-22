use crate::signatures;
use std::collections::HashMap;
use crate::structures::yaffs::{ parse_yaffs_obj_header, parse_yaffs_file_header };

const MIN_NUMBER_OF_OBJS: usize = 2;

pub const DESCRIPTION: &str = "YAFFS filesystem";

pub fn yaffs_magic() -> Vec<Vec<u8>> {
    return vec![
        b"\x03\x00\x00\x00\x01\x00\x00\x00\xFF\xFF\x00\x00".to_vec(),
        b"\x00\x00\x00\x03\x00\x00\x00\x01\xFF\xFF\x00\x00".to_vec(),
    ];
}

pub fn yaffs_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    const MAX_OBJ_SIZE: usize = 16896;
    const LITTLE_ENDIAN_FIRST_BYTE: u8 = 3;

    let mut result = signatures::common::SignatureResult {
                                            description: DESCRIPTION.to_string(),
                                            offset: offset,
                                            size: 0,
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };

    let mut endianness = "big";

    // Sanity check the amount of available data
    if file_data.len() >= (MAX_OBJ_SIZE * MIN_NUMBER_OF_OBJS) {
        // Detect endianness
        if file_data[offset] == LITTLE_ENDIAN_FIRST_BYTE {
            endianness = "little";
        }

        if let Ok((page_size, spare_size)) = get_page_spare_size(&file_data[offset..], endianness) {
            if let Ok(image_size) = get_image_size(&file_data[offset..], page_size, spare_size, endianness) {
                result.size = image_size;
                result.description = format!("{}, {} endian, page size: {}, spare size: {}, image size: {} bytes", result.description, endianness, page_size, spare_size, image_size);
                return Ok(result);
            }
        }
    }

    return Err(signatures::common::SignatureError);
}

// Returns a tuple of (page_size, spare_size)
fn get_page_spare_size(file_data: &[u8], endianness: &str) -> Result<(usize, usize), signatures::common::SignatureError> {
    let mut obj_sizes: Vec<usize> = vec![];
    let mut page_spare_lookup: HashMap<usize, (usize, usize)> = HashMap::new();

    let spare_sizes: Vec<usize> = vec![16, 32, 64, 128, 256, 512];
    let page_sizes: Vec<usize>= vec![512, 1024, 2048, 4096, 8192, 16384];

    /*
     * Build a list of possible "object sizes", which is the distance between the start of one object header and the next, by
     * adding each possible page size and spare section size together. Each combination of the two is unique, so detecting the
     * distance between two object headers corresponds directly to the page and spare size used when building this image.
     */
    for spare_size in spare_sizes {
        for page_size in &page_sizes {
            let obj_size = spare_size + page_size;
            obj_sizes.push(obj_size);
            page_spare_lookup.insert(obj_size, (*page_size, spare_size));
        }
    }

    // Sort the possible "object sizes" from smallest to largest
    obj_sizes.sort();

    // Try each "object size" value to determine the distance to the next object header
    for obj_size in obj_sizes {
        /* 
         * Parse the candidate header, if it is valid then we know the page and spare data sizes.
         * NOTE: Size of available file data is not sanity checked here, as yaffs_parser has already
         *       guarunteed that there is enough data for more than one object.
         */
        if let Ok(_header) = parse_yaffs_obj_header(&file_data[obj_size..], endianness) {
            return Ok(page_spare_lookup[&obj_size]);
        }
    }

    return Err(signatures::common::SignatureError);
}

// Returns the total size of the image, in bytes
fn get_image_size(file_data: &[u8], page_size: usize, spare_size: usize, endianness: &str) -> Result<usize, signatures::common::SignatureError> {
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
                    match get_file_block_count(&obj_data, page_size, endianness){
                        Err(e) => {
                            return Err(e);
                        },
                        Ok(block_count) => {
                            data_blocks += block_count;
                        },
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
            },
        }
    }

    // Sanity check the calculated image size
    if image_size > (block_size * MIN_NUMBER_OF_OBJS) && image_size <= file_data.len(){
        return Ok(image_size);
    }

    return Err(signatures::common::SignatureError);
}

// Returns the number of data blocks used to store file data; this size is only valid for file type objects
fn get_file_block_count(obj_data: &[u8], page_size: usize, endianness: &str) -> Result<usize, signatures::common::SignatureError> {
    // parse_yaffs_file_header only parses a portion of the header that we need; the partial structure starts this many bytes into the object data
    const INFO_STRUCT_START: usize = 268;

    // Parse the partial object header.
    if let Ok(file_info) = parse_yaffs_file_header(&obj_data[INFO_STRUCT_START..], endianness) {
        // File data is broken up into blocks of page_size bytes
        let file_block_count: usize = ((file_info.file_size as f64) / (page_size as f64)).ceil() as usize;
        return Ok(file_block_count);
    }

    return Err(signatures::common::SignatureError);
}
