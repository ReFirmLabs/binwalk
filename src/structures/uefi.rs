use crate::structures;

#[derive(Debug, Default, Clone)]
pub struct UEFIVolumeHeader {
    pub header_crc: usize,
    pub header_size: usize,
    pub volume_size: usize,
}

pub fn parse_uefi_volume_header(uefi_data: &[u8]) -> Result<UEFIVolumeHeader, structures::common::StructureError> {
    // UEFI volume starts with a 16-byte zero vector, followed by a 16-byte GUID, followed by the data structure defined below
    const UEFI_STRUCTURE_OFFSET: usize = 32;

    // Size of the uefi_pi_header_structure, defined below
    const UEFI_STRUCTURE_SIZE: usize = 28;

    // The revision field must be 2
    const EXPECTED_REVISION: usize = 2;

    let uefi_pi_header_structure = vec![
        ("volume_size", "u64"),
        ("magic", "u32"),
        ("attributes", "u32"),
        ("header_size", "u16"),
        ("header_crc", "u16"),
        ("extended_header_offset", "u16"),
        ("reserved", "u8"),
        ("revision", "u8"),
    ];

    // Sanity check the size of available data
    if uefi_data.len() >= (UEFI_STRUCTURE_OFFSET + UEFI_STRUCTURE_SIZE) {

        // Calculate the start and end offsets for parsing the header structure
        let header_struct_start = UEFI_STRUCTURE_OFFSET;
        let header_struct_end = header_struct_start + UEFI_STRUCTURE_SIZE;

        // Parse the volume header
        let uefi_volume_header = structures::common::parse(&uefi_data[header_struct_start..header_struct_end], &uefi_pi_header_structure, "little");

        // Make sure the header size is sane (must be smaller than the total volume size)
        if uefi_volume_header["header_size"] < uefi_volume_header["volume_size"] {
            // The reserved field *must* be 0
            if uefi_volume_header["reserved"] == 0 {
                // The revision number must be 2
                if uefi_volume_header["revision"] == EXPECTED_REVISION {

                    return Ok(UEFIVolumeHeader {
                        // TODO: Validate UEFI header CRC
                        header_crc: uefi_volume_header["header_crc"],
                        header_size: uefi_volume_header["header_size"],
                        volume_size: uefi_volume_header["volume_size"],
                    });
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}

#[derive(Debug, Default, Clone)]
pub struct UEFICapsuleHeader {
    pub total_size: usize,
    pub header_size: usize,
}

pub fn parse_uefi_capsule_header(uefi_data: &[u8]) -> Result<UEFICapsuleHeader, structures::common::StructureError> {
    const CAPSULE_STRUCTURE_SIZE: usize = 28;

    let uefi_capsule_structure = vec![
        ("guid_p1", "u64"),
        ("guid_p2", "u64"),
        ("header_size", "u32"),
        ("flags", "u32"),
        ("total_size", "u32"),
    ];

    // Sanity check on available data
    if uefi_data.len() > CAPSULE_STRUCTURE_SIZE {
        let header_start: usize = 0;
        let header_end: usize = header_start + CAPSULE_STRUCTURE_SIZE;

        // Parse the capsule header
        let capsule_header = structures::common::parse(&uefi_data[header_start..header_end], &uefi_capsule_structure, "little");

        // Sanity check on header and total size fields
        if capsule_header["header_size"] < capsule_header["total_size"] {

            return Ok(UEFICapsuleHeader {
                total_size: capsule_header["total_size"],
                header_size: capsule_header["header_size"],
            });
        }
    }

    return Err(structures::common::StructureError);
}
