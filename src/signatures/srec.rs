use crate::signatures;
use aho_corasick::AhoCorasick;

pub const SREC_DESCRIPTION: &str = "Motorola S-record";
pub const SREC_SHORT_DESCRIPTION: &str = "Motorola S-record (generic)";

pub fn srec_short_magic() -> Vec<Vec<u8>> {
    // Generic, short signature for s-records, should only be matched at the beginning of a file
    return vec![b"S0".to_vec()];
}

pub fn srec_magic() -> Vec<Vec<u8>> {
    // This assumes a srec header with the hex encoded string of "HDR"
    return vec![b"S00600004844521B".to_vec()];
}

pub fn srec_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    const UNIX_TERMINATING_CHARACTER: u8 = 0x0A;
    const WINDOWS_TERMINATING_CHARACTER: u8 = 0x0D;

    let mut result = signatures::common::SignatureResult {
                                            offset: offset,
                                            description: SREC_DESCRIPTION.to_string(),
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };

    // Srec lines, and hence the last line of an s-record, should end with a new line or line feed
    let terminating_characters = vec![WINDOWS_TERMINATING_CHARACTER, UNIX_TERMINATING_CHARACTER];

    // Possible srec footers
    let srec_footers = vec![
        b"\nS9",
        b"\nS8",
        b"\nS7",
    ];

    // Need to grep for the srec footer to determine total size
    let grep = AhoCorasick::new(srec_footers.clone()).unwrap();

    // Search for srec footer lines
    for srec_footer_match in grep.find_overlapping_iter(&file_data[offset..]) {

        // Assume origin OS is Unix unless proven otherwise
        let mut os_type: &str = "Unix";

        // Start searching for terminating EOF characters after this footer match (all footer signatures are the same size)
        let mut srec_eof: usize = offset + srec_footer_match.start() + srec_footers[0].len();

        // Found the start of a possible srec footer line, loop over remianing bytes looking for the line termination
        while srec_eof < file_data.len() {

            // All srec lines should end in \n or \r\n
            if terminating_characters.contains(&file_data[srec_eof]) {

                // Windows systems use \r\n
                if file_data[srec_eof] == WINDOWS_TERMINATING_CHARACTER {
                    // There should be one more character, a \n, which is common to both windows and linux implementations
                    srec_eof += 1;
                    os_type = "Windows";
                }

                // Sanity check, don't want to index out of bounds
                if srec_eof < file_data.len() {

                    // Last byte should be a line feed (\n)
                    if file_data[srec_eof] == UNIX_TERMINATING_CHARACTER {
                        // Include the final line feed byte in the size of the s-record
                        srec_eof += 1;

                        // Report results
                        result.size = srec_eof - offset;
                        result.description = format!("{}, origin OS: {}, total size: {} bytes", result.description, os_type, result.size);
                        return Ok(result);
                    }
                }

                // Invalid srec termination, stop searching
                return Err(signatures::common::SignatureError);
            }

            // Not a terminating character, go to the next byte in the file
            srec_eof += 1;
        }
    }
    
    // No valid srec footers found
    return Err(signatures::common::SignatureError);
}
