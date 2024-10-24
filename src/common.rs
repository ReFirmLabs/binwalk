//! Common Functions
use chrono::prelude::DateTime;
use log::{debug, error};
use std::fs::File;
use std::io::Read;

/// Read a file into memory and return its contents.
///
/// ## Example
///
/// ```
/// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_common_rs_11_0() -> Result<(), Box<dyn std::error::Error>> {
/// use binwalk::common::read_file;
///
/// let file_data = read_file("/etc/passwd")?;
/// assert!(file_data.len() > 0);
/// # Ok(())
/// # } _doctest_main_src_common_rs_11_0(); }
/// ```
pub fn read_file(file: impl Into<String>) -> Result<Vec<u8>, std::io::Error> {
    let mut file_data = Vec::new();
    let file_path = file.into();

    match File::open(&file_path) {
        Err(e) => {
            error!("Failed to open file {}: {}", file_path, e);
            Err(e)
        }
        Ok(mut fp) => match fp.read_to_end(&mut file_data) {
            Err(e) => {
                error!("Failed to read file {} into memory: {}", file_path, e);
                Err(e)
            }
            Ok(file_size) => {
                debug!("Loaded {} bytes from {}", file_size, file_path);
                Ok(file_data)
            }
        },
    }
}

/// Calculates the CRC32 checksum of the given data.
///
/// ## Notes
///
/// Uses initial CRC value of 0.
///
/// ## Example
///
/// ```
/// use binwalk::common::crc32;
///
/// let my_data: &[u8] = b"ABCD";
///
/// let my_data_crc = crc32(my_data);
///
/// assert_eq!(my_data_crc, 0xDB1720A5);
/// ```
pub fn crc32(data: &[u8]) -> u32 {
    crc32_v2::crc32(0, data)
}

/// Converts an epoch time to a formatted time string.
///
/// ## Example
///
/// ```
/// use binwalk::common::epoch_to_string;
///
/// let timestamp = epoch_to_string(0);
///
/// assert_eq!(timestamp, "1970-01-01 00:00:00");
/// ```
pub fn epoch_to_string(epoch_timestamp: u32) -> String {
    let date_time = DateTime::from_timestamp(epoch_timestamp.into(), 0);
    match date_time {
        Some(dt) => dt.format("%Y-%m-%d %H:%M:%S").to_string(),
        None => "".to_string(),
    }
}

/// Get a C-style NULL-terminated string from the provided list of u8 bytes.
/// Return value does not include the terminating NULL byte.
fn get_cstring_bytes(raw_data: &[u8]) -> Vec<u8> {
    let mut cstring: Vec<u8> = vec![];

    for raw_byte in raw_data {
        if *raw_byte == 0 {
            break;
        } else {
            cstring.push(*raw_byte);
        }
    }

    cstring
}

/// Get a C-style NULL-terminated string from the provided array of u8 bytes.
///
/// ## Example
///
/// ```
/// use binwalk::common::get_cstring;
///
/// let raw_data: &[u8] = b"this_is_a_c_string\x00";
///
/// let string = get_cstring(raw_data);
///
/// assert_eq!(string, "this_is_a_c_string");
/// ```
pub fn get_cstring(raw_data: &[u8]) -> String {
    let raw_string = get_cstring_bytes(raw_data);

    let string: String = match String::from_utf8(raw_string) {
        Err(_) => "".to_string(),
        Ok(s) => s.clone(),
    };

    string
}

/// Validates data offsets to prevent out-of-bounds access and infinite loops while parsing file formats.
///
/// ## Notes
///
/// - `next_offset` must be within the bounds of `available_data`
/// - `previous_offset` must be less than `next_offset`, or `None`
///
/// ## Example
///
/// ```
/// use binwalk::common::is_offset_safe;
///
/// let my_data: &[u8] = b"ABCD";
/// let available_data = my_data.len();
///
/// assert!(is_offset_safe(available_data, 0, None));
/// assert!(!is_offset_safe(available_data, 4, None));
/// assert!(is_offset_safe(available_data, 2, Some(1)));
/// assert!(!is_offset_safe(available_data, 2, Some(2)));
/// assert!(!is_offset_safe(available_data, 1, Some(2)));
/// ```
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

    true
}
