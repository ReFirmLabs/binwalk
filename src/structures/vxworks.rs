use crate::structures::common::{self, StructureError};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Stores info about a single VxWorks symbol table entry
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct VxWorksSymbolTableEntry {
    pub size: usize,
    pub name: usize,
    pub value: usize,
    pub symtype: String,
}

/// Parse a single VxWorks symbol table entry
pub fn parse_symtab_entry(
    symbol_data: &[u8],
    endianness: &str,
) -> Result<VxWorksSymbolTableEntry, StructureError> {
    // This *seems* to be the correct structure for a symbol table entry, it may be different for different VxWorks versions...
    let symtab_structure = vec![
        ("name_ptr", "u32"),
        ("value_ptr", "u32"),
        ("type", "u32"),
        ("group", "u32"),
    ];

    // There may be more types; these are the only ones I've found in the wild
    let allowed_symbol_types: HashMap<usize, String> = HashMap::from([
        (0x500, "function".to_string()),
        (0x700, "initialized data".to_string()),
        (0x900, "uninitialized data".to_string()),
    ]);

    let symtab_structure_size: usize = common::size(&symtab_structure);

    // Parse the symbol table entry
    if let Ok(symbol_entry) = common::parse(symbol_data, &symtab_structure, endianness) {
        // Sanity check expected values in the symbol table entry
        if allowed_symbol_types.contains_key(&symbol_entry["type"])
            && symbol_entry["name_ptr"] != 0
            && symbol_entry["value_ptr"] != 0
        {
            return Ok(VxWorksSymbolTableEntry {
                size: symtab_structure_size,
                name: symbol_entry["name_ptr"],
                value: symbol_entry["value_ptr"],
                symtype: allowed_symbol_types[&symbol_entry["type"]].clone(),
            });
        }
    }

    Err(StructureError)
}

/// Detect a symbol table entry's endianness
pub fn get_symtab_endianness(symbol_data: &[u8]) -> Result<String, StructureError> {
    const TYPE_FIELD_OFFSET: usize = 9;

    let mut endianness = "little";

    // The type field starts at offset 8 and is 0x00_00_05_00, so for big endian targets the 9th byte will be NULL
    if let Some(offset_field) = symbol_data.get(TYPE_FIELD_OFFSET) {
        if *offset_field == 0 {
            endianness = "big";
        }

        return Ok(endianness.to_string());
    }

    Err(StructureError)
}
