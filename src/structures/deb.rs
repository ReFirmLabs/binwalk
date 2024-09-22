use crate::structures;

#[derive(Debug, Clone, Default)]
pub struct DebHeader {
    pub file_size: usize,
}

pub fn parse_deb_header(deb_data: &[u8]) -> Result<DebHeader, structures::common::StructureError> {
    const END_MARKER_SIZE: usize = 2;
    const DATA_FILE_SIZE_LEN: usize = 10;
    const DATA_FILE_SIZE_OFFSET: usize = 48;
    const CONTROL_FILE_SIZE_END: usize = 130;
    const CONTROL_FILE_SIZE_START: usize = 120;

    let mut deb_header = DebHeader { ..Default::default() };

    // Sanity check the size of available data
    if deb_data.len() >= CONTROL_FILE_SIZE_END {
        // Index into the header to get the raw bytes of the decimal ASCII string that contains the control file size
        let control_file_size_data: Vec<u8> = deb_data[CONTROL_FILE_SIZE_START..CONTROL_FILE_SIZE_END].to_vec();

        // Convert the raw bytes into an ASCII string
        if let Ok(control_file_size_str) = String::from_utf8(control_file_size_data) {
            // Trim white space from the string and convert to an integer value
            if let Ok(control_file_size) = usize::from_str_radix(&control_file_size_str.trim(), 10) {
                // Calculate the offsets to the decimal ASCII string that contains the data file size
                let data_file_size_start: usize = CONTROL_FILE_SIZE_END + END_MARKER_SIZE + control_file_size + DATA_FILE_SIZE_OFFSET;
                let data_file_size_end: usize = data_file_size_start + DATA_FILE_SIZE_LEN;

                // Sanity check before indexing into deb_data
                if deb_data.len() > data_file_size_end {
                    // Index into the header to get the raw bytes of the deciaml ASCII string that contains the data file size
                    let data_file_size_data: Vec<u8> = deb_data[data_file_size_start..data_file_size_end].to_vec();

                    // Convert the raw bytes to an ASCII string
                    if let Ok(data_file_size_str) = String::from_utf8(data_file_size_data) {
                        // Trim whitespace from the string and convert to an integer value
                        if let Ok(data_file_size) = usize::from_str_radix(&data_file_size_str.trim(), 10) {
                            // Total file size is the end of the file data size ASCII field, plus the 2-byte end marker, plus the length of the following data file
                            // TODO: This size seems to be short by 2 bytes? Not a big deal for our purposes, but still...
                            deb_header.file_size = data_file_size_end + END_MARKER_SIZE + data_file_size;
                            return Ok(deb_header);
                        }
                    }
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}
