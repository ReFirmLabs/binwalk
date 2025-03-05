use crate::structures::common::{self, StructureError};
use std::collections::HashMap;

/// Struct to store some useful ELF info
#[derive(Debug, Default, Clone)]
pub struct ELFHeader {
    pub class: String,
    pub osabi: String,
    pub machine: String,
    pub exe_type: String,
    pub endianness: String,
}

/// Partially parses an ELF header
pub fn parse_elf_header(elf_data: &[u8]) -> Result<ELFHeader, StructureError> {
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

    // Just enough of the ELF structure to grab some useful info
    let elf_info_structure = vec![("type", "u16"), ("machine", "u16"), ("version", "u32")];

    let elf_classes = HashMap::from([(1, 32), (2, 64)]);

    let elf_endianness = HashMap::from([(1, "little"), (2, "big")]);

    let elf_osabi = HashMap::from([
        (0, "System-V (Unix)"),
        (1, "HP-UX"),
        (2, "NetBSD"),
        (3, "Linux"),
        (4, "GNU Hurd"),
        (5, "86Open"),
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
        (97, "ARM ABI"),
        (102, "Cell LV2"),
        (202, "Cafe OS"),
        (255, "embedded"),
    ]);

    let elf_types = HashMap::from([
        (0, "no file type"),
        (1, "relocatable"),
        (2, "executable"),
        (3, "shared object"),
        (4, "core file"),
    ]);

    let elf_machines = HashMap::from([
        (0, "no machine"),
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
        (11, "RS6000"),
        (15, "HP PA-RISC"),
        (16, "nCUBE"),
        (17, "Fujitsu VPP500"),
        (18, "SPARC32PLUS"),
        (19, "Intel 80960"),
        (20, "PowerPC"),
        (21, "PowerPC 64-bit"),
        (22, "S390"),
        (23, "IBM SPU/SPC"),
        (24, "cisco SVIP"),
        (25, "cisco 7200"),
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
        (80, "MMIX"),
        (81, "Harvard machine-independent"),
        (82, "SiTera Prism"),
        (83, "Atmel AVR 8-bit"),
        (84, "Fujitsu FR30"),
        (85, "Mitsubishi D10V"),
        (86, "Mitsubishi D30V"),
        (87, "NEC v850"),
        (88, "Renesas M32R"),
        (89, "Matsushita MN10300"),
        (90, "Matsushita MN10200"),
        (91, "picoJava"),
        (92, "OpenRISC"),
        (93, "Synopsys ARCompact ARC700 cores"),
        (94, "Tensilica Xtensa"),
        (95, "Alphamosaic VideoCore"),
        (96, "Thompson Multimedia"),
        (97, "NatSemi 32k"),
        (98, "Tenor Network TPC"),
        (99, "Trebia SNP 1000"),
        (100, "STMicroelectronics ST200"),
        (101, "Ubicom IP2022"),
        (102, "MAX Processor"),
        (103, "NatSemi CompactRISC"),
        (104, "Fujitsu F2MC16"),
        (105, "TI msp430"),
        (106, "Analog Devices Blackfin"),
        (107, "S1C33 Family of Seiko Epson"),
        (108, "Sharp embedded"),
        (109, "Arca RISC"),
        (110, "PKU-Unity Ltd."),
        (111, "eXcess: 16/32/64-bit"),
        (112, "Icera Deep Execution Processor"),
        (113, "Altera Nios II"),
        (114, "NatSemi CRX"),
        (115, "Motorola XGATE"),
        (116, "Infineon C16x/XC16x"),
        (117, "Renesas M16C series"),
        (118, "Microchip dsPIC30F"),
        (119, "Freescale RISC core"),
        (120, "Renesas M32C series"),
        (131, "Altium TSK3000 core"),
        (132, "Freescale RS08"),
        (134, "Cyan Technology eCOG2"),
        (135, "Sunplus S+core7 RISC"),
        (136, "New Japan Radio (NJR) 24-bit DSP"),
        (137, "Broadcom VideoCore III processor"),
        (138, "LatticeMico32"),
        (139, "Seiko Epson C17 family"),
        (140, "TMS320C6000"),
        (141, "TMS320C2000"),
        (142, "TMS320C55x"),
        (144, "TI Programmable Realtime Unit"),
        (160, "STMicroelectronics 64bit VLIW DSP"),
        (161, "Cypress M8C"),
        (162, "Renesas R32C series"),
        (163, "NXP TriMedia family"),
        (164, "Qualcomm DSP6"),
        (165, "Intel 8051 and variants"),
        (166, "STMicroelectronics STxP7x family"),
        (167, "Andes embedded RISC"),
        (168, "Cyan eCOG1X family"),
        (169, "Dallas MAXQ30"),
        (170, "New Japan Radio (NJR) 16-bit DSP"),
        (171, "M2000 Reconfigurable RISC"),
        (172, "Cray NV2 vector architecture"),
        (173, "Renesas RX family"),
        (174, "META"),
        (175, "MCST Elbrus e2k"),
        (176, "Cyan Technology eCOG16 family"),
        (177, "NatSemi CompactRISC"),
        (178, "Freescale Extended Time Processing Unit"),
        (179, "Infineon SLE9X"),
        (180, "Intel L1OM"),
        (181, "Intel K1OM"),
        (183, "ARM 64-bit"),
        (185, "Atmel 32-bit family"),
        (186, "STMicroeletronics STM8 8-bit"),
        (187, "Tilera TILE64"),
        (188, "Tilera TILEPro"),
        (189, "Xilinx MicroBlaze 32-bit RISC"),
        (190, "NVIDIA CUDA architecture"),
        (191, "Tilera TILE-Gx"),
        (195, "Synopsys ARCv2/HS3x/HS4x cores"),
        (197, "Renesas RL78 family"),
        (199, "Renesas 78K0R"),
        (200, "Freescale 56800EX"),
        (201, "Beyond BA1"),
        (202, "Beyond BA2"),
        (203, "XMOS xCORE"),
        (204, "Microchip 8-bit PIC(r)"),
        (210, "KM211 KM32"),
        (211, "KM211 KMX32"),
        (212, "KM211 KMX16"),
        (213, "KM211 KMX8"),
        (214, "KM211 KVARC"),
        (215, "Paneve CDP"),
        (216, "Cognitive Smart Memory"),
        (217, "iCelero CoolEngine"),
        (218, "Nanoradio Optimized RISC"),
        (219, "CSR Kalimba architecture family"),
        (220, "Zilog Z80"),
        (221, "Controls and Data Services VISIUMcore processor"),
        (
            222,
            "FTDI Chip FT32 high performance 32-bit RISC architecture",
        ),
        (223, "Moxie processor family"),
        (224, "AMD GPU architecture"),
        (243, "RISC-V"),
        (244, "Lanai 32-bit processor"),
        (245, "CEVA Processor Architecture Family"),
        (246, "CEVA X2 Processor Family"),
        (247, "Berkeley Packet Filter"),
        (248, "Graphcore Intelligent Processing Unit"),
        (249, "Imagination Technologies"),
        (250, "Netronome Flow Processor"),
        (251, "NEC Vector Engine"),
        (252, "C-SKY processor family"),
        (253, "Synopsys ARCv3 64-bit ISA/HS6x cores"),
        (254, "MOS Technology MCS 6502 processor"),
        (255, "Synopsys ARCv3 32-bit"),
        (256, "Kalray VLIW core of the MPPA family"),
        (257, "WDC 65C816"),
        (258, "LoongArch"),
        (259, "ChipON KungFu32"),
    ]);

    let mut elf_hdr_info = ELFHeader {
        ..Default::default()
    };

    // Endianness doesn't matter here, and we don't know what the ELF's endianness is yet
    if let Ok(e_ident) = common::parse(elf_data, &elf_ident_structure, "little") {
        // Sanity check the e_ident fields
        if e_ident["padding_1"] == 0
            && e_ident["padding_2"] == 0
            && e_ident["version"] == EXPECTED_VERSION
            && elf_classes.contains_key(&e_ident["class"])
            && elf_osabi.contains_key(&e_ident["osabi"])
            && elf_endianness.contains_key(&e_ident["endianness"])
        {
            // Set the ident info
            elf_hdr_info.class = elf_classes[&e_ident["class"]].to_string();
            elf_hdr_info.osabi = elf_osabi[&e_ident["osabi"]].to_string();
            elf_hdr_info.endianness = elf_endianness[&e_ident["endianness"]].to_string();

            // The rest of the ELF info comes immediately after the ident structure
            let elf_info_start: usize = ELF_IDENT_STRUCT_SIZE;
            let elf_info_end: usize = elf_info_start + ELF_INFO_STRUCT_SIZE;

            if let Some(elf_info_raw) = elf_data.get(elf_info_start..elf_info_end) {
                // Parse the remaining info from the ELF header
                if let Ok(elf_info) = common::parse(
                    elf_info_raw,
                    &elf_info_structure,
                    elf_endianness[&e_ident["endianness"]],
                ) {
                    // Sanity check the remaining ELF header fields
                    if elf_info["version"] == EXPECTED_VERSION
                        && elf_types.contains_key(&elf_info["type"])
                    {
                        // Set the ELF info fields
                        elf_hdr_info.exe_type = elf_types[&elf_info["type"]].to_string();
                        elf_hdr_info.machine = elf_machines
                            .get(&elf_info["machine"])
                            // Use 'Unknown' as a fallback for the machine type
                            .unwrap_or(&"Unknown")
                            .to_string();

                        return Ok(elf_hdr_info);
                    }
                }
            }
        }
    }

    Err(StructureError)
}
