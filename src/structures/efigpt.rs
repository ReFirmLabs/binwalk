use crate::common::{crc32, is_offset_safe};
use crate::structures::common::{self, StructureError};

const BLOCK_SIZE: usize = 512;

/// Struct to store EFI GPT header info
#[derive(Debug, Default, Clone)]
pub struct EFIGPTHeader {
    pub total_size: usize,
}

/// Parses an EFI GPT header
pub fn parse_efigpt_header(efi_data: &[u8]) -> Result<EFIGPTHeader, StructureError> {
    const EXPTECTED_REVISION: usize = 0x00010000;

    // https://uefi.org/sites/default/files/resources/UEFI_Spec_2_10_Aug29.pdf, p.116
    let efi_gpt_structure = vec![
        ("magic", "u64"),
        ("revision", "u32"),
        ("header_size", "u32"),
        ("header_crc", "u32"),
        ("reserved", "u32"),
        ("my_lba", "u64"),
        ("alternate_lba", "u64"),
        ("first_usable_lba", "u64"),
        ("last_usable_lba", "u64"),
        ("disk_guid_p1", "u64"),
        ("disk_guid_p2", "u64"),
        ("partition_entry_lba", "u64"),
        ("partition_entry_count", "u32"),
        ("partition_entry_size", "u32"),
        ("partition_entries_crc", "u32"),
    ];

    let mut result = EFIGPTHeader {
        ..Default::default()
    };

    // EFI GPT structure starts at the second block (first block is MBR)
    if let Some(gpt_data) = efi_data.get(BLOCK_SIZE..) {
        // Parse the EFI GPT structure
        if let Ok(gpt_header) = common::parse(gpt_data, &efi_gpt_structure, "little") {
            // Make sure the reserved field is NULL
            if gpt_header["reserved"] == 0 {
                // Make sure the revision field is the expected valid
                if gpt_header["revision"] == EXPTECTED_REVISION {
                    // Calculate the start and end offsets of the partition entries
                    let partition_entries_start: usize =
                        lba_to_offset(gpt_header["partition_entry_lba"]);
                    let partition_entries_end: usize = partition_entries_start
                        + (gpt_header["partition_entry_count"]
                            * gpt_header["partition_entry_size"]);

                    // Get the partition entires
                    if let Some(partition_entries_data) =
                        efi_data.get(partition_entries_start..partition_entries_end)
                    {
                        // Validate the partition entries' CRC
                        if crc32(partition_entries_data)
                            == (gpt_header["partition_entries_crc"] as u32)
                        {
                            let mut next_partition_offset = 0;
                            let mut previous_partition_offset = None;
                            let available_data = partition_entries_data.len();

                            // Loop through all partition entries
                            while is_offset_safe(
                                available_data,
                                next_partition_offset,
                                previous_partition_offset,
                            ) {
                                if let Some(partition) = parse_gpt_partition_entry(
                                    &partition_entries_data[next_partition_offset..],
                                ) {
                                    // EOF is the end of the farthest away partition
                                    if partition.start_offset < partition.end_offset
                                        && partition.end_offset > result.total_size
                                    {
                                        result.total_size = partition.end_offset;
                                    }
                                }

                                previous_partition_offset = Some(next_partition_offset);
                                next_partition_offset += gpt_header["partition_entry_size"];
                            }

                            if result.total_size > 0 {
                                return Ok(result);
                            }
                        }
                    }
                }
            }
        }
    }

    Err(StructureError)
}

#[derive(Debug, Default, Clone)]
struct GPTPartitionEntry {
    pub end_offset: usize,
    pub start_offset: usize,
}

/// Parse a GPT partition entry
fn parse_gpt_partition_entry(entry_data: &[u8]) -> Option<GPTPartitionEntry> {
    let entry_structure = vec![
        ("type_guid_p1", "u64"),
        ("type_guid_p2", "u64"),
        ("partition_guid_p1", "u64"),
        ("partition_guid_p2", "u64"),
        ("starting_lba", "u64"),
        ("ending_lba", "u64"),
        ("attributes", "u64"),
    ];

    let mut result = GPTPartitionEntry {
        ..Default::default()
    };

    if let Ok(entry_header) = common::parse(entry_data, &entry_structure, "little") {
        // GUID types of NULL can be ignored
        if entry_header["type_guid_p1"] != 0 && entry_header["type_guid_p2"] != 0 {
            result.start_offset = lba_to_offset(entry_header["starting_lba"]);
            result.end_offset = lba_to_offset(entry_header["ending_lba"]);
            return Some(result);
        }
    }

    None
}

// Convert LBA to offset
fn lba_to_offset(lba: usize) -> usize {
    lba * BLOCK_SIZE
}
