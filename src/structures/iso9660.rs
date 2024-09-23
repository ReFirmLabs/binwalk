use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct ISOHeader {
    pub image_size: usize,
}

pub fn parse_iso_header(iso_data: &[u8]) -> Result<ISOHeader, structures::common::StructureError> {
    // Offset from the beginning of the ISO image to the start of iso_structure
    const ISO_STRUCT_START: usize = 32840;

    // Offset from the beginning of the ISO image to the end of iso_structure
    const ISO_STRUCT_END: usize = 32908;

    // Partial ISO header structure, enough to reasonably validate that this is not a false positive and to calculate the total ISO size
    let iso_structure = vec![
        ("unused1", "u64"),
        ("volume_size_lsb", "u32"),
        ("volume_size_msb", "u32"),
        ("unused2", "u64"),
        ("unused3", "u64"),
        ("unused4", "u64"),
        ("unused5", "u64"),
        ("set_size_lsb", "u16"),
        ("set_size_msb", "u16"),
        ("sequence_number_lsb", "u16"),
        ("sequence_number_msb", "u16"),
        ("block_size_lsb", "u16"),
        ("block_size_msb", "u16"),
        ("path_table_size_lsb", "u32"),
        ("path_table_size_msb", "u32"),
    ];

    let mut iso_info = ISOHeader {
        ..Default::default()
    };

    if iso_data.len() >= ISO_STRUCT_END {
        let iso_header = structures::common::parse(
            &iso_data[ISO_STRUCT_START..ISO_STRUCT_END],
            &iso_structure,
            "little",
        );

        // Make sure all the unused fields are, in fact, unused
        if iso_header["unused1"] == 0
            && iso_header["unused2"] == 0
            && iso_header["unused3"] == 0
            && iso_header["unused4"] == 0
            && iso_header["unused5"] == 0
        {
            /*
             * Make sure all the identical, but byte-swapped, fields agree.
             * NOTE: The to_be() as usizeas usizeconversions probably won't work on big-endian systems.
             */
            if iso_header["set_size_lsb"] == (iso_header["set_size_msb"] as u16).to_be() as usize
                && iso_header["block_size_lsb"]
                    == (iso_header["block_size_msb"] as u16).to_be() as usize
                && iso_header["volume_size_lsb"]
                    == (iso_header["volume_size_msb"] as u32).to_be() as usize
                && iso_header["sequence_number_lsb"]
                    == (iso_header["sequence_number_msb"] as u16).to_be() as usize
                && iso_header["path_table_size_lsb"]
                    == (iso_header["path_table_size_msb"] as u32).to_be() as usize
            {
                iso_info.image_size = iso_header["volume_size_lsb"] * iso_header["block_size_lsb"];
                return Ok(iso_info);
            }
        }
    }

    return Err(structures::common::StructureError);
}
