use crate::common::is_offset_safe;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use aho_corasick::AhoCorasick;

/// Human readable descriptions
pub const SREC_DESCRIPTION: &str = "Motorola S-record";
pub const SREC_SHORT_DESCRIPTION: &str = "Motorola S-record (generic)";

/// Generic, short signature for s-records, should only be matched at the beginning of a file
pub fn srec_short_magic() -> Vec<Vec<u8>> {
    vec![b"S0".to_vec()]
}

/// This assumes a srec header with the hex encoded string of "HDR"
pub fn srec_magic() -> Vec<Vec<u8>> {
    vec![b"S00600004844521B".to_vec()]
}

/// Validates a SREC signature
pub fn srec_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    // \r and \n
    const UNIX_TERMINATING_CHARACTER: u8 = 0x0A;
    const WINDOWS_TERMINATING_CHARACTER: u8 = 0x0D;

    let mut result = SignatureResult {
        offset,
        description: SREC_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let available_data = file_data.len();

    // Srec lines, and hence the last line of an s-record, should end with a new line or line feed
    let terminating_characters = [WINDOWS_TERMINATING_CHARACTER, UNIX_TERMINATING_CHARACTER];

    // Possible srec footers
    let srec_footers = vec![b"\nS9", b"\nS8", b"\nS7"];

    // Need to grep for the srec footer to determine total size
    let grep = AhoCorasick::new(srec_footers.clone()).unwrap();

    // Search for srec footer lines
    for srec_footer_match in grep.find_overlapping_iter(&file_data[offset..]) {
        // Assume origin OS is Unix unless proven otherwise
        let mut os_type: &str = "Unix";

        // Start searching for terminating EOF characters after this footer match (all footer signatures are the same size)
        let mut srec_eof: usize = offset + srec_footer_match.start() + srec_footers[0].len();
        let mut last_srec_eof = None;

        // Found the start of a possible srec footer line, loop over remianing bytes looking for the line termination
        while is_offset_safe(available_data, srec_eof, last_srec_eof) {
            // All srec lines should end in \n or \r\n
            if terminating_characters.contains(&file_data[srec_eof]) {
                // Windows systems use \r\n
                if file_data[srec_eof] == WINDOWS_TERMINATING_CHARACTER {
                    // There should be one more character, a \n, which is common to both windows and linux implementations
                    srec_eof += 1;
                    os_type = "Windows";
                }

                // Sanity check, don't want to index out of bounds
                if let Some(srec_last_byte) = file_data.get(srec_eof) {
                    // Last byte should be a line feed (\n)
                    if *srec_last_byte == UNIX_TERMINATING_CHARACTER {
                        // Include the final line feed byte in the size of the s-record
                        srec_eof += 1;

                        // Report results
                        result.size = srec_eof - offset;
                        result.description = format!(
                            "{}, origin OS: {}, total size: {} bytes",
                            result.description, os_type, result.size
                        );
                        return Ok(result);
                    }
                }

                // Invalid srec termination, stop searching
                return Err(SignatureError);
            }

            // Not a terminating character, go to the next byte in the file
            last_srec_eof = Some(srec_eof);
            srec_eof += 1;
        }
    }

    // No valid srec footers found
    Err(SignatureError)
}
