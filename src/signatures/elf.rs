use crate::signatures;
use crate::structures::elf::parse_elf_header;

pub const DESCRIPTION: &str = "ELF binary";

pub fn elf_magic() -> Vec<Vec<u8>> {
    return vec![b"\x7FELF".to_vec()];
}

pub fn elf_parser(
    file_data: &Vec<u8>,
    offset: usize,
) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {
    let mut result = signatures::common::SignatureResult {
        size: 0,
        offset: offset,
        name: "elf".to_string(),
        description: DESCRIPTION.to_string(),
        confidence: signatures::common::CONFIDENCE_MEDIUM,
        ..Default::default()
    };

    if let Ok(elf_header) = parse_elf_header(&file_data[offset..]) {
        result.description = format!(
            "{}, {}-bit {}, {} for {}, {} endian",
            result.description,
            elf_header.class,
            elf_header.exe_type,
            elf_header.machine,
            elf_header.osabi,
            elf_header.endianness
        );
        return Ok(result);
    }

    return Err(signatures::common::SignatureError);
}
