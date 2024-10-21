use crate::structures::common::StructureError;

/// Struct to store DEB file info
#[derive(Debug, Clone, Default)]
pub struct DebHeader {
    pub file_size: usize,
}

/// Parse a DEB file
pub fn parse_deb_header(deb_data: &[u8]) -> Result<DebHeader, StructureError> {
    const END_MARKER_SIZE: usize = 2;
    const DATA_FILE_SIZE_LEN: usize = 10;
    const DATA_FILE_SIZE_OFFSET: usize = 48;
    const CONTROL_FILE_SIZE_END: usize = 130;
    const CONTROL_FILE_SIZE_START: usize = 120;

    let mut deb_header = DebHeader {
        ..Default::default()
    };

    // Index into the header to get the raw bytes of the decimal ASCII string that contains the control file size
    if let Some(control_file_size_data) =
        deb_data.get(CONTROL_FILE_SIZE_START..CONTROL_FILE_SIZE_END)
    {
        // Convert the raw bytes into an ASCII string
        if let Ok(control_file_size_str) = String::from_utf8(control_file_size_data.to_vec()) {
            // Trim white space from the string and convert to an integer value
            if let Ok(control_file_size) = control_file_size_str.trim().parse::<usize>() {
                // Calculate the offsets to the decimal ASCII string that contains the data file size
                let data_file_size_start: usize = CONTROL_FILE_SIZE_END
                    + END_MARKER_SIZE
                    + control_file_size
                    + DATA_FILE_SIZE_OFFSET;
                let data_file_size_end: usize = data_file_size_start + DATA_FILE_SIZE_LEN;

                // Index into the header to get the raw bytes of the deciaml ASCII string that contains the data file size
                if let Some(data_file_size_data) =
                    deb_data.get(data_file_size_start..data_file_size_end)
                {
                    // Convert the raw bytes to an ASCII string
                    if let Ok(data_file_size_str) = String::from_utf8(data_file_size_data.to_vec())
                    {
                        // Trim whitespace from the string and convert to an integer value
                        if let Ok(data_file_size) = data_file_size_str.trim().parse::<usize>() {
                            // Total file size is the end of the file data size ASCII field, plus the 2-byte end marker, plus the length of the following data file
                            // TODO: This size seems to be short by 2 bytes? Not a big deal for our purposes, but still...
                            deb_header.file_size =
                                data_file_size_end + END_MARKER_SIZE + data_file_size;
                            return Ok(deb_header);
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}
