use crate::common::crc32;
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
                            // Alternate GPT header is at the end of the EFI GPT, and is one block in size
                            result.total_size = lba_to_offset(gpt_header["alternate_lba"] + 1);
                            return Ok(result);
                        }
                    }
                }
            }
        }
    }

    return Err(StructureError);
}

// Convert LBA to offset
fn lba_to_offset(lba: usize) -> usize {
    return lba * BLOCK_SIZE;
}
