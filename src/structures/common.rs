use std::collections::HashMap;

/*
 * Note that all values returned by the parse() function are of type usize; this is a concious decision.
 * Returning usize types makes the calling code much cleaner, but that means that u64 fields won't fit into the return value on 32-bit systems.
 * Thus, only 64-bit systems are supported. This requirement is enforced here.
 */
#[cfg(not(target_pointer_width = "64"))]
compile_error!("compilation is only allowed for 64-bit targets");

#[derive(Debug, Clone)]
pub struct StructureError;

/*
 * Function to parse basic data structures.
 *
 * Supported data types: u8, u16, u24, u32, u64.
 *
 * data: The raw data to apply the structure over. It is up to the caller to ensure that enough data is provided to parse the entire structure.
 * structure: A vector of tuples describing the data structure (see below for exmaple).
 * endianness: One of: "big", "little".
 *
 * Example:
 *
 *  let my_structure = vec![
 *      ("magic", "u32"),
 *      ("size", "u64"),
 *      ("flags", "u8"),
 *      ("checksum", "u32"),
 *  ];
 *
 *  let some_data = b"AAAA\x01\x00\x00\x00\x00\x00\x00\x00\x08\x01\x02\x03\x04";
 *  let header = structure::parse(some_data, &my_structure, "little");
 *  println!("Reported size is: {}", header["size"]);
 *
 */
pub fn parse(
    data: &[u8],
    structure: &Vec<(&str, &str)>,
    endianness: &str,
) -> Result<HashMap<String, usize>, StructureError> {
    const U24_SIZE: usize = 3;

    let mut value: usize;
    let mut csize: usize;
    let mut offset: usize = 0;
    let mut parsed_structure = HashMap::new();

    // Get the size of the defined structure
    let structure_size = size(structure);

    if let Some(raw_data) = data.get(0..structure_size) {
        for (name, ctype) in structure {
            let data_type: String = ctype.to_string();

            csize = type_to_size(&ctype);

            if csize == std::mem::size_of::<u8>() {
                // u8, endianness doesn't matter
                value = u8::from_be_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                    as usize;
            } else if csize == std::mem::size_of::<u16>() {
                if endianness == "big" {
                    value = u16::from_be_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                } else {
                    value = u16::from_le_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                }

            // Yes Virginia, u24's are real
            } else if csize == U24_SIZE {
                if endianness == "big" {
                    value = ((raw_data[offset] as usize) << 16)
                        + ((raw_data[offset + 1] as usize) << 8)
                        + (raw_data[offset + 2] as usize);
                } else {
                    value = ((raw_data[offset + 2] as usize) << 16)
                        + ((raw_data[offset + 1] as usize) << 8)
                        + (raw_data[offset] as usize);
                }
            } else if csize == std::mem::size_of::<u32>() {
                if endianness == "big" {
                    value = u32::from_be_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                } else {
                    value = u32::from_le_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                }
            } else if csize == std::mem::size_of::<u64>() {
                if endianness == "big" {
                    value = u64::from_be_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                } else {
                    value = u64::from_le_bytes(raw_data[offset..offset + csize].try_into().unwrap())
                        as usize;
                }
            } else {
                panic!(
                    "Cannot parse structure element with unknown data type '{}'",
                    data_type
                );
            }

            offset += csize;
            parsed_structure.insert(name.to_string(), value);
        }

        return Ok(parsed_structure);
    }

    return Err(StructureError);
}

/*
 * Returns the size of a given structure definition.
 */
pub fn size(structure: &Vec<(&str, &str)>) -> usize {
    let mut struct_size: usize = 0;

    for (_name, ctype) in structure {
        struct_size += type_to_size(ctype);
    }

    return struct_size;
}

fn type_to_size(ctype: &str) -> usize {
    // This table must be updated when new data types are added
    let size_lookup_table: HashMap<&str, usize> =
        HashMap::from([("u8", 1), ("u16", 2), ("u24", 3), ("u32", 4), ("u64", 8)]);

    if size_lookup_table.contains_key(ctype) == false {
        panic!("Unknown size for structure type '{}'!", ctype);
    }

    return size_lookup_table[ctype];
}
