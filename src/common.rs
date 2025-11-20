//! Common Functions
use log::{debug, error};
use std::path::Path;

/// Read a file data into memory and return its contents.
///
/// ## Example
///
/// ```
/// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_common_rs_48_0() -> Result<(), Box<dyn std::error::Error>> {
/// use binwalk_ng::common::read_file;
///
/// let file_data = read_file("/etc/passwd")?;
/// assert!(file_data.len() > 0);
/// # Ok(())
/// # } _doctest_main_src_common_rs_48_0(); }
/// ```
pub fn read_file(file: impl AsRef<Path>) -> Result<Vec<u8>, std::io::Error> {
    let file_path = file.as_ref();

    let file_data = std::fs::read(&file_path)
        .inspect_err(|e| error!("Failed to read file {} into memory: {e}", file_path.display()))?;

    let file_size = file_data.len();
    debug!("Loaded {file_size} bytes from {}", file_path.display());
    Ok(file_data)
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
/// use binwalk_ng::common::crc32;
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
/// use binwalk_ng::common::epoch_to_string;
///
/// let timestamp = epoch_to_string(0);
///
/// assert_eq!(timestamp, "1970-01-01 00:00:00");
/// ```
pub fn epoch_to_string(epoch_timestamp: impl Into<i64>) -> String {
    match jiff::Timestamp::new(epoch_timestamp.into(), 0) {
        Ok(timestamp) => timestamp.strftime("%Y-%m-%d %H:%M:%S").to_string(),
        Err(_) => "".to_string(),
    }
}

/// Get a C-style NULL-terminated string from the provided array of u8 bytes.
///
/// ## Example
///
/// ```
/// use binwalk_ng::common::get_cstring;
///
/// let raw_data: &[u8] = b"this_is_a_c_string\x00";
///
/// let string = get_cstring(raw_data);
///
/// assert_eq!(string, "this_is_a_c_string");
/// ```
pub fn get_cstring(raw_data: &[u8]) -> String {
    let first_zero = raw_data.iter().position(|&r| r == 0).unwrap_or(raw_data.len());
    let raw_bytes = &raw_data[..first_zero];
    String::from_utf8_lossy(raw_bytes).into_owned()
}

/// Returns true if the provided byte is a printable ASCII character
///
/// ## Example
///
/// ```
/// use binwalk_ng::common::is_printable_ascii;
///
/// assert!(is_printable_ascii(0x41));
/// assert!(!is_printable_ascii(0xFE));
/// ```
pub fn is_printable_ascii(b: u8) -> bool {
    const ASCII_MIN: u8 = 0x0A;
    const ASCII_MAX: u8 = 0x7E;

    (ASCII_MIN..=ASCII_MAX).contains(&b)
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
/// use binwalk_ng::common::is_offset_safe;
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
    if last_offset.is_some_and(|b| b >= next_offset) {
        return false;
    }

    // Ensure that the next file offset is within the bounds of available file data
    if next_offset >= available_data {
        return false;
    }

    true
}
