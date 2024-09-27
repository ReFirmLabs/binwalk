use chrono::prelude::DateTime;
use crc32_v2;
use log::{debug, error};
use std::fs::File;
use std::io::Read;

/*
 * Read a file into memory and return its contents.
 */
pub fn read_file(file_path: &String) -> Result<Vec<u8>, std::io::Error> {
    let mut file_data = Vec::new();

    match File::open(file_path) {
        Err(e) => {
            error!("Failed to open file {}: {}", file_path, e);
            return Err(e);
        }
        Ok(mut fp) => match fp.read_to_end(&mut file_data) {
            Err(e) => {
                error!("Failed to read file {} into memory: {}", file_path, e);
                return Err(e);
            }
            Ok(file_size) => {
                debug!("Loaded {} bytes from {}", file_size, file_path);
                return Ok(file_data);
            }
        },
    }
}

/*
 * Calculates the CRC32 checksum of the given data.
 * Uses initial CRC value of 0.
 */
pub fn crc32(data: &[u8]) -> u32 {
    return crc32_v2::crc32(0, data);
}

/*
 * Converts an epoch time to a formatted time string.
 * Returns the formatted time string; returns an empty string on error.
 */
pub fn epoch_to_string(epoch_timestamp: u32) -> String {
    let date_time = DateTime::from_timestamp(epoch_timestamp.into(), 0);
    match date_time {
        Some(dt) => return dt.format("%Y-%m-%d %H:%M:%S").to_string(),
        None => return "".to_string(),
    }
}

/*
 * Get a C-style NULL-terminated string from the provided list of u8 bytes.
 * Return value does not include the terminating NULL byte.
 */
pub fn get_cstring_bytes(raw_data: &[u8]) -> Vec<u8> {
    let mut cstring: Vec<u8> = vec![];

    for raw_byte in raw_data {
        if *raw_byte == 0 {
            break;
        } else {
            cstring.push(*raw_byte);
        }
    }

    return cstring;
}

/*
 * Get a C-style NULL-terminated string from the provided list of u8 bytes.
 * Return value is a UTF-8 String.
 */
pub fn get_cstring(raw_data: &[u8]) -> String {
    let string: String;

    let raw_string = get_cstring_bytes(raw_data);

    match String::from_utf8(raw_string) {
        Err(_) => string = "".to_string(),
        Ok(s) => string = s.clone(),
    }

    return string;
}

/*
 * Validates file/data offsets to prevent out-of-bounds access and infinite loops.
 *
 * available_data - The maximum number of bytes available in the data being accessed
 * next_offset    - The next data offset to be accessed
 * last_offset    - The previous data offset that was accessed
 */
pub fn is_offset_safe(
    available_data: usize,
    next_offset: usize,
    last_offset: Option<usize>,
) -> bool {
    // If a previous file offset was specified, ensure that it is less than the next file offset
    if let Some(previous_offset) = last_offset {
        if previous_offset >= next_offset {
            return false;
        }
    }

    // Ensure that the next file offset is within the bounds of available file data
    if next_offset >= available_data {
        return false;
    }

    return true;
}
