use crate::structures;
use std::collections::HashMap;

pub struct PEHeader {
    pub machine: String,
}

pub fn parse_pe_header(pe_data: &[u8]) -> Result<PEHeader, structures::common::StructureError> {
    const PE_MAGIC: usize = 0x00004550;

    let dos_structure = vec![
        ("e_magic", "u16"),    // "MZ"
        ("e_cblp", "u16"),     // Bytes on last page of file
        ("e_cp", "u16"),       // Pages in file
        ("e_crlc", "u16"),     // Relocations
        ("e_cparhdr", "u16"),  // Header size, in paragraphs
        ("e_minalloc", "u16"), // Min extra paragraphs needed
        ("e_maxalloc", "u16"), // Max extra paragraphs needed
        ("e_ss", "u16"),       // Initial relative SS value
        ("e_sp", "u16"),       // Initial SP value
        ("e_csum", "u16"),     // Checksum
        ("e_ip", "u16"),       // Initial IP value
        ("e_cs", "u16"),       // Initial relative CS value
        ("e_lfarlc", "u16"),   // File address of relocation table
        ("e_ovno", "u16"),     // Overlay number
        ("e_res_1", "u16"),
        ("e_res_2", "u16"),
        ("e_res_3", "u16"),
        ("e_res_4", "u16"),
        ("e_oemid", "u16"),   // OEM identifier
        ("e_oeminfo", "u16"), // OEM specific information
        ("e_res_5", "u16"),
        ("e_res_6", "u16"),
        ("e_res_7", "u16"),
        ("e_res_8", "u16"),
        ("e_res_9", "u16"),
        ("e_res_10", "u16"),
        ("e_res_11", "u16"),
        ("e_res_12", "u16"),
        ("e_res_13", "u16"),
        ("e_res_14", "u16"),
        ("e_lfanew", "u32"), // Offset to the PE header
    ];

    let pe_structure = vec![
        ("magic", "u32"),
        ("machine", "u16"),
        ("number_of_sections", "u16"),
        ("timestamp", "u32"),
        ("symbol_table_ptr", "u32"),
        ("number_of_symbols", "u32"),
        ("optional_header_size", "u16"),
        ("characteristics", "u16"),
    ];

    let known_machine_types: HashMap<usize, &str> = HashMap::from([
        (0, "Unknown"),
        (0x184, "Alpha32"),
        (0x284, "Alpha64"),
        (0x1D3, "Matsushita AM33"),
        (0x8664, "Intel x86-64"),
        (0x1C0, "ARM"),
        (0xAA64, "ARM-64"),
        (0x1C4, "ARM Thumb2"),
        (0xEBC, "EFI"),
        (0x14C, "Intel x86"),
        (0x200, "Intel Itanium"),
        (0x6232, "LoongArch 32-bit"),
        (0x6264, "LoongArch 64-bit"),
        (0x9041, "Mitsubishi M32R"),
        (0x266, "MIPS16"),
        (0x366, "MIPS with FPU"),
        (0x466, "MIPS16 with FPU"),
        (0x1F0, "PowerPC"),
        (0x1F1, "PowerPC with FPU"),
        (0x5032, "RISC-V 32-bit"),
        (0x5064, "RISC-V 64-bit"),
        (0x5128, "RISC-V 128-bit"),
        (0x1A2, "Hitachi SH3"),
        (0x1A3, "Hitachi SH3 DSP"),
        (0x1A6, "Hitachi SH4"),
        (0x1A8, "Hitachi SH5"),
        (0x1C2, "Thumb"),
        (0x169, "MIPS WCEv2"),
    ]);

    // Structure sizes
    let pe_header_size = structures::common::size(&pe_structure);
    let dos_header_size = structures::common::size(&dos_structure);

    // Start and end offsets of the DOS header
    let dos_header_start: usize = 0;
    let dos_header_end: usize = dos_header_start + dos_header_size;

    // Sanity check the size of available data
    if pe_data.len() > dos_header_end {
        // Parse the DOS header
        let dos_header = structures::common::parse(
            &pe_data[dos_header_start..dos_header_end],
            &dos_structure,
            "little",
        );

        // Sanity check the reserved header fields; they should all be 0
        if dos_header["e_res_1"] == 0
            && dos_header["e_res_2"] == 0
            && dos_header["e_res_3"] == 0
            && dos_header["e_res_4"] == 0
            && dos_header["e_res_5"] == 0
            && dos_header["e_res_6"] == 0
            && dos_header["e_res_7"] == 0
            && dos_header["e_res_8"] == 0
            && dos_header["e_res_9"] == 0
            && dos_header["e_res_10"] == 0
            && dos_header["e_res_11"] == 0
            && dos_header["e_res_12"] == 0
            && dos_header["e_res_13"] == 0
            && dos_header["e_res_14"] == 0
        {
            // Start and end offsets of the PE header
            let pe_header_start: usize = dos_header["e_lfanew"];
            let pe_header_end: usize = pe_header_start + pe_header_size;

            // Sanity check the PE header offsets
            if pe_header_start > dos_header_end && pe_data.len() > pe_header_end {
                // Parse the second part of the header
                let pe_header = structures::common::parse(
                    &pe_data[pe_header_start..pe_header_end],
                    &pe_structure,
                    "little",
                );

                // Check the PE magic bytes
                if pe_header["magic"] == PE_MAGIC {
                    // Check the reported machine type
                    if known_machine_types.contains_key(&pe_header["machine"]) {
                        return Ok(PEHeader {
                            machine: known_machine_types[&pe_header["machine"]].to_string(),
                        });
                    }
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}
