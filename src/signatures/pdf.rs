use crate::signatures;

pub const DESCRIPTION: &str = "PDF document";

pub fn pdf_magic() -> Vec<Vec<u8>> {
    // This assumes a major version of 1
    return vec![b"%PDF-1.".to_vec()];
}

pub fn pdf_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    // More than enough data for our needs
    const MIN_PDF_SIZE: usize = 16;

    const NEWLINE_OFFSET: usize = 8;
    const PERCENT_OFFSET: usize = 9;
    const MINOR_NUMBER_OFFSET: usize = 7;

    const ASCII_ZERO: u8 = 0x30;
    const ASCII_NINE: u8 = 0x39;
    const ASCII_NEWLINE: u8 = 0x0A;
    const ASCII_PERCENT: u8 = 0x25;
    const ASCII_CARRIGE_RETURN: u8 = 0x0D;

    let mut result = signatures::common::SignatureResult {
        description: DESCRIPTION.to_string(),
        offset: offset,
        size: 0,
        ..Default::default()
    };

    // Sanity check the size of available data
    if file_data.len() >= (offset + MIN_PDF_SIZE) {
        let mut win_shift = 0;

        // PDF header is expected to start with something like: %PDF-1.7\n%
        let newline: u8 = file_data[offset + NEWLINE_OFFSET];

        // Windows does \r\n, not just \n
        if newline == ASCII_CARRIGE_RETURN {
            win_shift = 1;
        }

        let percent: u8 = file_data[offset + PERCENT_OFFSET + win_shift];
        let version_minor: u8 = file_data[offset + MINOR_NUMBER_OFFSET];

        // Very basic validation
        if version_minor <= ASCII_NINE && version_minor >= ASCII_ZERO {
            if percent == ASCII_PERCENT {
                if newline == ASCII_NEWLINE || newline == ASCII_CARRIGE_RETURN {
                    let os_string: String;

                    if win_shift == 1 {
                        os_string = "Windows".to_string();
                    } else {
                        os_string = "Unix".to_string();
                    }

                    result.description = format!(
                        "{}, version 1.{}, created on a {} system",
                        result.description,
                        version_minor - ASCII_ZERO,
                        os_string
                    );

                    return Ok(result);
                }
            }
        }
    }

    return Err(signatures::common::SignatureError);
}
