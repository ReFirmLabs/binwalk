use crate::structures;
use std::collections::HashMap;

#[derive(Debug, Default, Clone)]
pub struct ELFHeader {
    pub class: String,
    pub osabi: String,
    pub machine: String,
    pub exe_type: String,
    pub endianness: String,
}

pub fn parse_elf_header(elf_data: &[u8]) -> Result<ELFHeader, structures::common::StructureError> {
    // Smallest possible 32bit ELF (according to the internet)
    const MIN_ELF_SIZE: usize = 45;

    const ELF_INFO_STRUCT_SIZE: usize = 8;
    const ELF_IDENT_STRUCT_SIZE: usize = 16;

    const EXPECTED_VERSION: usize = 1;

    let elf_ident_structure = vec![
        ("magic", "u32"),
        ("class", "u8"),
        ("endianness", "u8"),
        ("version", "u8"),
        ("osabi", "u8"),
        ("abiversion", "u8"),
        ("padding_1", "u32"),
        ("padding_2", "u24"),
    ];

    // Just enough of the ELF structure to grab some system info
    let elf_info_structure = vec![("type", "u16"), ("machine", "u16"), ("version", "u32")];

    let elf_classes = HashMap::from([(1, 32), (2, 64)]);

    let elf_endianness = HashMap::from([(1, "little"), (2, "big")]);

    let elf_osabi = HashMap::from([
        (0, "System-V (Unix)"),
        (1, "HP-UX"),
        (2, "NetBSD"),
        (3, "Linux"),
        (4, "GNU Hurd"),
        (6, "Solaris"),
        (7, "AIX"),
        (8, "IRIX"),
        (9, "FreeBSD"),
        (10, "Tru64"),
        (11, "Novell Modesto"),
        (12, "OpenBSD"),
        (13, "OpenVMS"),
        (14, "NonStop Kernel"),
        (15, "AROS"),
        (16, "FenixOS"),
        (17, "Nuxi CloudABI"),
        (18, "OpenVOS"),
    ]);

    let elf_types = HashMap::from([
        (1, "relocatable"),
        (2, "executable"),
        (3, "shared object"),
        (4, "core file"),
    ]);

    let elf_machines = HashMap::from([
        (1, "AT&T WE 32100"),
        (2, "SPARC"),
        (3, "x86"),
        (4, "Motorola 68k"),
        (5, "Motorola 88k"),
        (6, "Intel MCU"),
        (7, "Intel 80860"),
        (8, "MIPS"),
        (9, "IBM System/370"),
        (10, "MIPS RS3000"),
        (15, "HP PA-RISC"),
        (19, "Intel 80960"),
        (20, "PowerPC"),
        (21, "PowerPC 64-bit"),
        (22, "S390"),
        (23, "IBM SPU/SPC"),
        (36, "NEC V800"),
        (37, "Fujitsu FR20"),
        (38, "TRW RH-32"),
        (39, "Motorola RCE"),
        (40, "ARM"),
        (41, "Digital Alpha"),
        (42, "SuperH"),
        (43, "SPARCv9"),
        (44, "Siemens TriCore embedded processor"),
        (45, "Argonaut RISC Core"),
        (46, "Hitachi H8/300"),
        (47, "Hitachi H8/300H"),
        (48, "Hitachi H8S"),
        (49, "Hitachi H8/500"),
        (50, "IA-64"),
        (51, "Stanford MIPS-X"),
        (52, "Motorola ColdFire"),
        (53, "Motorola M68HC12"),
        (54, "Fujitsu MMA Multimedia Accelerator"),
        (55, "Siemens PCP"),
        (56, "Sony nCPU embedded RISC processor"),
        (57, "Denso NDR1 microprocessor"),
        (58, "Motorola StarCore"),
        (59, "Toyota ME16"),
        (60, "STMicroelectronics ST100"),
        (61, "Advanced Logic TinyJ embedded processor"),
        (62, "AMD X86-64"),
        (63, "Sony DSP processor"),
        (64, "PDP-10"),
        (65, "PDP-11"),
        (66, "Siemens FX66"),
        (67, "STMicroelectronics ST9+"),
        (68, "STMicroelectronics ST7"),
        (69, "Motorola MC68HC16"),
        (70, "Motorola MC68HC11"),
        (71, "Motorola MC68HC08"),
        (72, "Motorola MC68HC05"),
        (73, "Silicon Graphics SVx"),
        (74, "STMicroelectonrics ST19"),
        (75, "Digital VAX"),
        (76, "Axis Communications 32-bit CPU"),
        (77, "Infineon Technologies 32-bit CPU"),
        (78, "Element 14 64-bit DSP"),
        (79, "LSI Logic 16-bit DSP"),
        (94, "Tensilica Xtensa"),
        (140, "TMS320C6000"),
        (175, "MCST Elbrus e2k"),
        (183, "ARM 64-bit"),
        (220, "Zilog Z80"),
        (243, "RISC-V"),
        (247, "Berkeley Packet Filter"),
        (257, "WDC 65C816"),
        (258, "LoongArch"),
    ]);

    let mut elf_hdr_info = ELFHeader {
        ..Default::default()
    };

    // Sanity check the size of available data
    if elf_data.len() >= MIN_ELF_SIZE {
        // Endianness doesn't matter here, and we don't know what the ELF's endianness is yet
        let e_ident = structures::common::parse(
            &elf_data[0..ELF_IDENT_STRUCT_SIZE],
            &elf_ident_structure,
            "little",
        );

        // Sanity check the e_ident fields
        if e_ident["padding_1"] == 0 && e_ident["padding_2"] == 0 {
            if e_ident["version"] == EXPECTED_VERSION {
                if elf_classes.contains_key(&e_ident["class"]) {
                    if elf_osabi.contains_key(&e_ident["osabi"]) {
                        if elf_endianness.contains_key(&e_ident["endianness"]) {
                            // Set the ident info
                            elf_hdr_info.class = elf_classes[&e_ident["class"]].to_string();
                            elf_hdr_info.osabi = elf_osabi[&e_ident["osabi"]].to_string();
                            elf_hdr_info.endianness =
                                elf_endianness[&e_ident["endianness"]].to_string();

                            // The rest of the ELF info comes immediately after the ident structure
                            let elf_info_start: usize = ELF_IDENT_STRUCT_SIZE;
                            let elf_info_end: usize = elf_info_start + ELF_INFO_STRUCT_SIZE;

                            // Parse the remaining info from the ELF header
                            let elf_info = structures::common::parse(
                                &elf_data[elf_info_start..elf_info_end],
                                &elf_info_structure,
                                elf_endianness[&e_ident["endianness"]],
                            );

                            // Sanity check the remaining ELF header fields
                            if elf_info["version"] == EXPECTED_VERSION {
                                if elf_types.contains_key(&elf_info["type"]) {
                                    if elf_machines.contains_key(&elf_info["machine"]) {
                                        // Set the ELF info, erm, info
                                        elf_hdr_info.exe_type =
                                            elf_types[&elf_info["type"]].to_string();
                                        elf_hdr_info.machine =
                                            elf_machines[&elf_info["machine"]].to_string();

                                        return Ok(elf_hdr_info);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return Err(structures::common::StructureError);
}
