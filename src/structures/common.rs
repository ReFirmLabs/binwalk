use log::error;
use std::collections::HashMap;

/*
 * Note that all values returned by the parse() function are of type usize; this is a concious decision.
 * Returning usize types makes the calling code much cleaner, but that means that u64 fields won't fit into the return value on 32-bit systems.
 * Thus, only 64-bit systems are supported. This requirement is enforced here.
 */
#[cfg(not(target_pointer_width = "64"))]
compile_error!("compilation is only allowed for 64-bit targets");

/// Error return value of structure parsers
#[derive(Debug, Clone)]
pub struct StructureError;

/// Function to parse basic C-style data structures.
///
/// ## Supported Data Types
///
/// The following data types are supported:
/// - u8
/// - u16
/// - u24
/// - u32
/// - u64
///
/// ## Arguments
///
/// - `data`: The raw data to apply the structure over
/// - `structure`: A vector of tuples describing the data structure
/// - `endianness`: One of: "big", "little"
///
/// ## Example:
///
/// ```
/// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_structures_common_rs_34_0() -> Result<bool, binwalk_ng::structures::common::StructureError> {
/// use binwalk_ng::structures;
///
/// let my_structure = vec![
///     ("magic", "u32"),
///     ("size", "u64"),
///     ("flags", "u8"),
///     ("packed_bytes", "u24"),
///     ("checksum", "u16"),
/// ];
///
/// let some_data = b"AAAA\x01\x00\x00\x00\x00\x00\x00\x00\x08\x0A\x0B\x0C\x01\x02";
/// let header = structures::common::parse(some_data, &my_structure, "little")?;
///
/// assert_eq!(header["magic"], 0x41414141);
/// assert_eq!(header["checksum"], 0x0201);
/// # Ok(true)
/// # } _doctest_main_src_structures_common_rs_34_0(); }
/// ```
pub fn parse(
    data: &[u8],
    structure: &[(&str, &str)],
    endianness: &str,
) -> Result<HashMap<String, usize>, StructureError> {
    const U8_SIZE: usize = std::mem::size_of::<u8>();
    const U16_SIZE: usize = std::mem::size_of::<u16>();
    const U32_SIZE: usize = std::mem::size_of::<u32>();
    const U64_SIZE: usize = std::mem::size_of::<u64>();
    const U24_SIZE: usize = 3;

    let mut parsed_structure = HashMap::with_capacity(structure.len());

    let mut remaining_data = data;
    for &(name, ctype) in structure {
        let csize = type_to_size(ctype).ok_or(StructureError)?;
        let raw_bytes = remaining_data.split_off(..csize).ok_or(StructureError)?;
        let value = match csize {
            // u8, endianness doesn't matter
            U8_SIZE => usize::from(raw_bytes[0]),
            U16_SIZE => {
                let f = if endianness == "big" {
                    u16::from_be_bytes
                } else {
                    u16::from_le_bytes
                };
                usize::from(f(raw_bytes.try_into().unwrap()))
            }
            U32_SIZE => {
                let f = if endianness == "big" {
                    u32::from_be_bytes
                } else {
                    u32::from_le_bytes
                };
                f(raw_bytes.try_into().unwrap()) as usize
            }
            U64_SIZE => {
                let f = if endianness == "big" {
                    u64::from_be_bytes
                } else {
                    u64::from_le_bytes
                };
                f(raw_bytes.try_into().unwrap()) as usize // TODO: this will truncate on 32 bit
            }
            // Yes Virginia, u24's are real
            U24_SIZE => {
                if endianness == "big" {
                    usize::from(raw_bytes[0]) << 16
                        | usize::from(raw_bytes[1]) << 8
                        | usize::from(raw_bytes[2])
                } else {
                    usize::from(raw_bytes[2]) << 16
                        | usize::from(raw_bytes[1]) << 8
                        | usize::from(raw_bytes[0])
                }
            }
            _ => {
                error!("Cannot parse structure element with unknown data type '{ctype}'");
                return Err(StructureError);
            }
        };

        parsed_structure.insert(name.to_string(), value);
    }

    Ok(parsed_structure)
}

/// Returns the size of a given structure definition.
///
/// ## Example:
///
/// ```
/// use binwalk_ng::structures;
///
/// let my_structure = vec![
///     ("magic", "u32"),
///     ("size", "u64"),
///     ("flags", "u8"),
///     ("checksum", "u32"),
/// ];
///
/// let struct_size = structures::common::size(&my_structure);
///
/// assert_eq!(struct_size, 17);
/// ```
pub fn size(structure: &[(&str, &str)]) -> usize {
    let mut struct_size: usize = 0;

    for (_name, ctype) in structure {
        match type_to_size(ctype) {
            None => continue,
            Some(member_size) => {
                struct_size += member_size;
            }
        }
    }

    struct_size
}

fn type_to_size(ctype: &str) -> Option<usize> {
    match ctype {
        "u8" => Some(1),
        "u16" => Some(2),
        "u24" => Some(3),
        "u32" => Some(4),
        "u64" => Some(8),
        _ => {
            error!("Unknown size for structure type '{ctype}'!");
            None
        }
    }
}
