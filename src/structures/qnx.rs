use crate::structures;

pub struct IFSHeader {
    pub total_size: usize,
}

pub fn parse_ifs_header(ifs_data: &[u8]) -> Result<IFSHeader, structures::common::StructureError> {
    const IFS_HEADER_SIZE: usize = 64;

    // https://github.com/askac/dumpifs/blob/master/sys/startup.h
    let ifs_structure = vec![
        ("magic", "u32"),
        ("version", "u16"),
        ("flags1", "u8"),
        ("flags2", "u8"),
        ("header_size", "u16"),
        ("machine", "u16"),
        ("startup_vaddr", "u32"),
        ("paddr_bias", "u32"),
        ("image_paddr", "u32"),
        ("ram_paddr", "u32"),
        ("ram_size", "u32"),
        ("startup_size", "u32"),
        ("stored_size", "u32"),
        ("imagefs_paddr", "u32"),
        ("imagefs_size", "u32"),
        ("preboot_size", "u16"),
        ("zero_0", "u16"),
        ("zero_1", "u32"),
        ("zero_2", "u32"),
        ("zero_3", "u32"),
    ];

    // Sanity check the size of available data
    if ifs_data.len() >= IFS_HEADER_SIZE {
        // Parse the IFS header
        let ifs_header =
            structures::common::parse(&ifs_data[0..IFS_HEADER_SIZE], &ifs_structure, "little");

        // The flags2 field is unused and should be 0
        if ifs_header["flags2"] == 0 {
            // Verify that all the zero fields are, in fact, zero
            if ifs_header["zero_0"] == 0
                && ifs_header["zero_1"] == 0
                && ifs_header["zero_2"] == 0
                && ifs_header["zero_3"] == 0
            {
                return Ok(IFSHeader {
                    total_size: ifs_header["stored_size"],
                });
            }
        }
    }

    return Err(structures::common::StructureError);
}
