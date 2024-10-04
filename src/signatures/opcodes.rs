use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_MEDIUM};
use capstone::prelude::*;
use capstone::Capstone;
use capstone::Endian;
use log::error;

/// Human readable description
pub const DESCRIPTION: &str = "CPU opcodes";

/// Type definition for disassembler functions
type Disassembler = fn() -> Result<Capstone, SignatureError>;

/// Stores relevant info about an opcode signature
#[derive(Debug, Clone)]
struct OpCode {
    /// The magic bytes to search for
    pub magic: Vec<u8>,
    /// The offset of the magic bytes from the beginning of the opcode
    pub offset: usize,
    /// Number of bytes to disassemble
    pub size: usize,
    /// Number of instructions that should be disassembled
    pub insns: usize,
    /// Function to build the relevant disassembler
    pub disassembler: Disassembler,
    /// Human readable description of this opcode signature
    pub description: String,
}

/// Returns a list of OpCode definition structures
fn supported_opcodes() -> Vec<OpCode> {
    // Define an OpCode instance for each CPU opcode signature
    let opcode_definitions: Vec<OpCode> = vec![
        // MIPS32 big endian function prologue
        OpCode {
            magic: b"\x27\xBD\xFF".to_vec(),
            offset: 0,
            size: 8,
            insns: 2,
            disassembler: mips_be,
            description: "MIPS 32 bit big endian function prologue".to_string(),
        },
        // MIPS32 little endian function prologue
        OpCode {
            magic: b"\xFF\xBD\x27".to_vec(),
            offset: 1,
            size: 8,
            insns: 2,
            disassembler: mips_le,
            description: "MIPS 32 bit little endian function prologue".to_string(),
        },
        // x86 function prologue
        OpCode {
            // move ebp, esp
            // push edi
            magic: b"\x55\x89\xE5".to_vec(),
            offset: 0,
            size: 3,
            insns: 2,
            disassembler: x86_32,
            description: "Intel 32 bit function prologue".to_string(),
        },
        // x86 endbr32
        OpCode {
            magic: b"\xF3\x0F\x1E\xFB".to_vec(),
            offset: 0,
            size: 4,
            insns: 1,
            disassembler: x86_32,
            description: "Intel 32 bit indirect branch termination".to_string(),
        },
        // x86_64 function prologue
        OpCode {
            // push rbp
            // move rbp, rsp
            magic: b"\x55\x48\x89\xE5".to_vec(),
            offset: 0,
            size: 4,
            insns: 2,
            disassembler: x86_64,
            description: "Intel 64 bit function prologue".to_string(),
        },
        // x86_64 endbr64
        OpCode {
            magic: b"\xF3\x0F\x1E\xFA".to_vec(),
            offset: 0,
            size: 4,
            insns: 1,
            disassembler: x86_64,
            description: "Intel 64 bit indirect branch termination".to_string(),
        },
        // ARM32 LE function call
        OpCode {
            // blx
            magic: b"\xFF\xF7".to_vec(),
            offset: 0,
            size: 8,
            insns: 2,
            disassembler: arm_le,
            description: "ARM 32 bit little endian function call".to_string(),
        },
        // ARM32 BE function prologue
        OpCode {
            // STMFD SP!, {XX}
            magic: b"\xE9\x2D".to_vec(),
            offset: 0,
            size: 8,
            insns: 2,
            disassembler: arm_be,
            description: "ARM 32 bit big endian function prologue".to_string(),
        },
        // ARM32 LE function return
        OpCode {
            // ret
            magic: b"\xC0\x03\x5F\xD6".to_vec(),
            offset: 0,
            size: 4,
            insns: 1,
            disassembler: arm64_le,
            description: "ARM 64 bit little endian function return".to_string(),
        },
    ];

    return opcode_definitions;
}

/// Magic signatures for various CPU opcodes
pub fn opcode_magic() -> Vec<Vec<u8>> {
    let mut opcode_magics: Vec<Vec<u8>> = vec![];

    for opcode_definition in supported_opcodes() {
        opcode_magics.push(opcode_definition.magic.clone());
    }

    return opcode_magics;
}

/// Validates CPU opcode signatures
pub fn opcode_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<SignatureResult, SignatureError> {
    // Successful return value
    let mut result = SignatureResult {
        confidence: CONFIDENCE_MEDIUM,
        description: DESCRIPTION.to_string(),
        ..Default::default()
    };

    // Loop through all supported opcode definitions
    for opcode_definition in supported_opcodes() {
        if let Some(match_bytes) = file_data.get(offset..offset + opcode_definition.magic.len()) {
            // If the sample bytes match the magic bytes defined here, let's try to disassemble them
            if match_bytes == opcode_definition.magic {
                // Calculate the start and end offsets for this opcode
                let opcode_start = offset - opcode_definition.offset;
                let opcode_end = opcode_start + opcode_definition.size;

                // Get the opcode raw bytes
                if let Some(raw_opcode_bytes) = file_data.get(opcode_start..opcode_end) {
                    // Build this CPU disassembler instance
                    if let Ok(cs) = (opcode_definition.disassembler)() {
                        // Attempt to disassemble the bytes
                        if let Ok(insns) = cs.disasm_all(raw_opcode_bytes, 0) {
                            // If the number of disassembled instructions equals the expected number of instructions, consider this signature valid
                            if insns.len() == opcode_definition.insns {
                                result.offset = opcode_start;
                                result.size = opcode_definition.size;
                                result.description = format!(
                                    "{}: {}",
                                    result.description, opcode_definition.description
                                );
                                return Ok(result);
                            }
                        }
                    }
                }
            }
        }
    }

    return Err(SignatureError);
}

/// Insantiates Capstone for MIPS32 BE
fn mips_be() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .mips()
        .mode(arch::mips::ArchMode::Mips32)
        .endian(Endian::Big)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for MIPS32 LE
fn mips_le() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .mips()
        .mode(arch::mips::ArchMode::Mips32)
        .endian(Endian::Little)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for 32-bit Intel
fn x86_32() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .x86()
        .mode(arch::x86::ArchMode::Mode32)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for 64-bit Intel
fn x86_64() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .x86()
        .mode(arch::x86::ArchMode::Mode64)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for 32-bit ARM
fn arm_le() -> Result<Capstone, SignatureError> {
    match Capstone::new().arm().mode(arch::arm::ArchMode::Arm).build() {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for 32-bit ARMBE
fn arm_be() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .arm()
        .mode(arch::arm::ArchMode::Arm)
        .endian(Endian::Big)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}

/// Insantiates Capstone for 64-bit ARM
fn arm64_le() -> Result<Capstone, SignatureError> {
    match Capstone::new()
        .arm64()
        .mode(arch::arm64::ArchMode::Arm)
        .build()
    {
        Err(e) => {
            error!("Failed to initialize Capstone: {}", e);
            return Err(SignatureError);
        }
        Ok(cs) => {
            return Ok(cs);
        }
    }
}
