use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct CabinetHeader {
    pub total_size: usize,
    pub header_size: usize,
    pub file_count: usize,
    pub folder_count: usize,
}

pub fn parse_cab_header(header_data: &[u8]) -> Result<CabinetHeader, structures::common::StructureError> {

    const MAJOR_VERSION: usize = 1;
    const MINOR_VERSION: usize = 3;
    const FLAG_EXTRA_DATA_PRESENT: usize = 4;

    const CAB_STRUCT_SIZE: usize = 40;
    const CAB_EXTRA_STRUCT_SIZE: usize = 20;

    let cab_header_structure = vec![
        ("magic", "u32"),
        ("reserved1", "u32"),
        ("size", "u32"),
        ("reserved2", "u32"),
        ("first_file_offset", "u32"),
        ("reserved3", "u32"),
        ("minor_version", "u8"),
        ("major_version", "u8"),
        ("folder_count", "u16"),
        ("file_count", "u16"),
        ("flags", "u16"),
        ("id", "u16"),
        ("set_number", "u16"),
        ("extra_header_size", "u16"),
        ("cbCFFolder", "u8"),
        ("cbCFData", "u8"),

    ];

    let cab_extra_header_structure = vec![
        ("unknown1", "u32"),
        ("data_offset", "u32"),
        ("data_size", "u32"),
        ("unknown2", "u32"),
        ("unknown3", "u32")
    ];

    let available_data: usize = header_data.len();
    let mut header_info = CabinetHeader { header_size: CAB_STRUCT_SIZE, ..Default::default() };

    // Sanity check the size of available data
    if available_data > CAB_STRUCT_SIZE {
        // Parse the CAB header
        let cab_header = structures::common::parse(&header_data[0..CAB_STRUCT_SIZE], &cab_header_structure, "little");

        // All reserved fields must be 0
        if cab_header["reserved1"] == 0 && cab_header["reserved2"] == 0 && cab_header["reserved3"] == 0 {
            // Version must be 1.3
            if cab_header["major_version"] == MAJOR_VERSION && cab_header["minor_version"] == MINOR_VERSION {
                // Update the CabinetHeader fields
                header_info.total_size = cab_header["size"];
                header_info.file_count = cab_header["file_count"];
                header_info.folder_count = cab_header["folder_count"];

                // Make sure the reported size is sane
                if header_info.total_size <= available_data {
                    // Assume everything is *not* ok, until proven otherwise
                    let mut everything_ok: bool = false;

                    // If the extra data flag was set, we need to parse the extra data header to get the size of the extra data
                    if (cab_header["flags"] & FLAG_EXTRA_DATA_PRESENT) != 0 && cab_header["extra_header_size"] == CAB_EXTRA_STRUCT_SIZE {
                        // Calclate the start and end of the extra header
                        let extra_header_start: usize = CAB_STRUCT_SIZE;
                        let extra_header_end: usize = extra_header_start + CAB_EXTRA_STRUCT_SIZE;

                        // Sanity check available data
                        if header_data.len() > extra_header_end {
                            // Parse the header
                            let extra_header = structures::common::parse(&header_data[extra_header_start..extra_header_end], &cab_extra_header_structure, "little");

                            // The extra data is expected to come immediately after the data specified in the main CAB header
                            if extra_header["data_offset"] == cab_header["size"] {
                                // Update the CAB file size to include the extra data
                                header_info.total_size += extra_header["data_size"];
                                everything_ok = true;
                            }
                        }
                    } else {
                        everything_ok = true;
                    }

                    // If everything checked out OK, return the result
                    if everything_ok == true {
                        return Ok(header_info);
                    }
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}
