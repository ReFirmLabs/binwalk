use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct DMGFooter {
    pub footer_size: usize,
    pub data_offset: usize,
    pub xml_offset: usize,
}

pub fn parse_dmg_footer(dmg_data: &[u8]) -> Result<DMGFooter, structures::common::StructureError> {
    // https://newosxbook.com/DMG.html
    let dmg_footer_structure = vec![
        ("magic", "u32"),
        ("version", "u32"),
        ("header_size", "u32"),
        ("flags", "u32"),
        ("running_data_fork_offset", "u64"),
        ("data_fork_offset", "u64"),
        ("data_fork_length", "u64"),
        ("rsrc_fork_offset", "u64"),
        ("rsrc_fork_length", "u64"),
        ("segment_number", "u32"),
        ("segment_count", "u32"),
        ("segment_id_p1", "u64"),
        ("segment_id_p2", "u64"),
        ("data_checksum_type", "u32"),
        ("data_checksum_size", "u32"),
        ("data_checksum_1", "u32"),
        ("data_checksum_2", "u32"),
        ("data_checksum_3", "u32"),
        ("data_checksum_4", "u32"),
        ("data_checksum_5", "u32"),
        ("data_checksum_6", "u32"),
        ("data_checksum_7", "u32"),
        ("data_checksum_8", "u32"),
        ("data_checksum_9", "u32"),
        ("data_checksum_10", "u32"),
        ("data_checksum_11", "u32"),
        ("data_checksum_12", "u32"),
        ("data_checksum_13", "u32"),
        ("data_checksum_14", "u32"),
        ("data_checksum_15", "u32"),
        ("data_checksum_16", "u32"),
        ("data_checksum_17", "u32"),
        ("data_checksum_18", "u32"),
        ("data_checksum_19", "u32"),
        ("data_checksum_20", "u32"),
        ("data_checksum_21", "u32"),
        ("data_checksum_22", "u32"),
        ("data_checksum_23", "u32"),
        ("data_checksum_24", "u32"),
        ("data_checksum_25", "u32"),
        ("data_checksum_26", "u32"),
        ("data_checksum_27", "u32"),
        ("data_checksum_28", "u32"),
        ("data_checksum_29", "u32"),
        ("data_checksum_30", "u32"),
        ("data_checksum_31", "u32"),
        ("data_checksum_32", "u32"),
        ("xml_offset", "u64"),
        ("xml_length", "u64"),
        ("reserved_1", "u64"),
        ("reserved_2", "u64"),
        ("reserved_3", "u64"),
        ("reserved_4", "u64"),
        ("reserved_5", "u64"),
        ("reserved_6", "u64"),
        ("reserved_7", "u64"),
        ("reserved_8", "u64"),
        ("reserved_9", "u64"),
        ("reserved_10", "u64"),
        ("reserved_11", "u64"),
        ("reserved_12", "u64"),
        ("reserved_13", "u64"),
        ("reserved_14", "u64"),
        ("reserved_15", "u64"),
        ("checksum_type", "u32"),
        ("checksum_size", "u32"),
        ("checksum_1", "u32"),
        ("checksum_2", "u32"),
        ("checksum_3", "u32"),
        ("checksum_4", "u32"),
        ("checksum_5", "u32"),
        ("checksum_6", "u32"),
        ("checksum_7", "u32"),
        ("checksum_8", "u32"),
        ("checksum_9", "u32"),
        ("checksum_10", "u32"),
        ("checksum_11", "u32"),
        ("checksum_12", "u32"),
        ("checksum_13", "u32"),
        ("checksum_14", "u32"),
        ("checksum_15", "u32"),
        ("checksum_16", "u32"),
        ("checksum_17", "u32"),
        ("checksum_18", "u32"),
        ("checksum_19", "u32"),
        ("checksum_20", "u32"),
        ("checksum_21", "u32"),
        ("checksum_22", "u32"),
        ("checksum_23", "u32"),
        ("checksum_24", "u32"),
        ("checksum_25", "u32"),
        ("checksum_26", "u32"),
        ("checksum_27", "u32"),
        ("checksum_28", "u32"),
        ("checksum_29", "u32"),
        ("checksum_30", "u32"),
        ("checksum_31", "u32"),
        ("checksum_32", "u32"),
        ("image_variant", "u32"),
        ("sector_count", "u64"),
        ("reserved_16", "u32"),
        ("reserved_17", "u32"),
        ("reserved_18", "u32"),
    ];

    let structure_size: usize = structures::common::size(&dmg_footer_structure);

    // Sanity check, make sure there is enough data to parse the footer structure
    if dmg_data.len() >= structure_size {
        // Parse the DMG footer
        let dmg_footer = structures::common::parse(&dmg_data, &dmg_footer_structure, "big");

        // Sanity check, make sure the reported header size is the size of this structure
        if dmg_footer["header_size"] == structure_size {
            return Ok(DMGFooter {
                data_offset: dmg_footer["data_fork_offset"],
                xml_offset: dmg_footer["xml_offset"],
                footer_size: structure_size,
            });
        }
    }

    return Err(structures::common::StructureError);
}
