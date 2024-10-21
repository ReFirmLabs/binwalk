use crate::structures::common::{self, StructureError};

/// Struct to store PCHROM image info
#[derive(Debug, Default, Clone)]
pub struct PCHRomHeader {
    pub data_size: usize,
    pub header_size: usize,
}

/// Parse a PCHROM header
pub fn parse_pchrom_header(pch_data: &[u8]) -> Result<PCHRomHeader, StructureError> {
    // Structure is a fixed size, at a fixed offset from the beginning of the PCHROM image
    const HEADER_STRUCTURE_SIZE: usize = 8;
    const HEADER_STRUCTURE_OFFSET: usize = 16;

    // All "expected" values are derived from the Intel PCH Programming Manual
    const EXPECTED_FCBA: usize = 3;
    const EXPECTED_FRBA: usize = 4;

    let expected_nc_values: Vec<usize> = vec![0, 1];

    let pch_rom_header_structure = vec![
        ("flmagic", "u32"),
        ("flmap0_fcba", "u8"),
        ("flmap0_nc", "u8"),
        ("flmap0_frba_nr", "u16"),
    ];

    // Calculate the header structure start and end offsets
    let struct_start: usize = HEADER_STRUCTURE_OFFSET;
    let struct_end: usize = struct_start + HEADER_STRUCTURE_SIZE;

    if let Some(pch_structure_data) = pch_data.get(struct_start..struct_end) {
        // Parse the header structure
        if let Ok(pch_header) =
            common::parse(pch_structure_data, &pch_rom_header_structure, "little")
        {
            // Sanity check the expected header values
            if pch_header["flmap0_fcba"] == EXPECTED_FCBA
                && pch_header["flmap0_frba_nr"] == EXPECTED_FRBA
                && expected_nc_values.contains(&pch_header["flmap0_nc"])
            {
                // Parse the flash rom region entries to determine the total image size
                if let Ok(pch_regions_size) =
                    get_pch_regions_size(pch_data, 0, pch_header["flmap0_fcba"])
                {
                    return Ok(PCHRomHeader {
                        header_size: HEADER_STRUCTURE_OFFSET,
                        data_size: pch_regions_size,
                    });
                }
            }
        }
    }

    Err(StructureError)
}

/// Determine the total size of PCHROM regions
fn get_pch_regions_size(
    pch_data: &[u8],
    offset: usize,
    fcba: usize,
) -> Result<usize, StructureError> {
    // There are 5 defined flash regions: Descriptor, BIOS, ME, GBE, PDATA
    const FLASH_REGION_COUNT: usize = 5;

    // Each entry is a 32-bit value describing the region
    const FLASH_REGION_ENTRY_SIZE: usize = 4;

    // There is a 32-bit entry for each possible region in the PCH image
    let region_entry_structure = vec![("region_value", "u32")];

    let mut image_size: usize = 0;

    // The base address of the flash regions is encoded into 8 bits of the FCBA header field, like so
    let flash_region_base_address: usize = ((fcba >> 16) & 0xFF) << 4;

    // Region entries are 32-bit values stored seqeuntially starting at the flash region base address
    for i in 0..FLASH_REGION_COUNT {
        // Get the offset of the next region's 32-bit entry
        let region_entry_start = offset + flash_region_base_address + (i * FLASH_REGION_ENTRY_SIZE);
        let region_entry_end = region_entry_start + FLASH_REGION_ENTRY_SIZE;

        // Get the next region's 32-bit value, in raw bytes
        match pch_data.get(region_entry_start..region_entry_end) {
            None => {
                return Err(StructureError);
            }
            Some(pch_region_data) => {
                // Parse the 32-bit entry value for this region
                if let Ok(region_entry) =
                    common::parse(pch_region_data, &region_entry_structure, "little")
                {
                    let region_value = region_entry["region_value"];

                    // The base (starting offset) and limit (ending offset) of the region is encoded into the 32-bit entry value
                    let region_base = (region_value & 0x1FFF) << 12;
                    let region_limit = (((region_value & 0x1FFF0000) >> 4) | 0xFFFF) + 1;

                    // Size can be inferred from the base and limit values
                    let region_size = region_limit - region_base;

                    // If size is 0, this region is not used in this image
                    if region_size > 0 && region_limit > image_size {
                        image_size = region_limit;
                    }
                }
            }
        }
    }

    if image_size > 0 {
        return Ok(image_size);
    }

    Err(StructureError)
}
