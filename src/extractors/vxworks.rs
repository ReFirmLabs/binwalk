use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::vxworks::{
    get_symtab_endianness, parse_symtab_entry, VxWorksSymbolTableEntry,
};
use serde_json;

/// Describes the VxWorks symbol table extractor
pub fn vxworks_symtab_extractor() -> Extractor {
    Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_symbol_table),
        ..Default::default()
    }
}

/// Internal extractor for writing VxWorks symbol tables to JSON
pub fn extract_symbol_table(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const MIN_VALID_ENTRIES: usize = 250;
    const OUTFILE_NAME: &str = "symtab.json";

    let mut result = ExtractionResult {
        ..Default::default()
    };

    let available_data = file_data.len();
    let mut previous_entry_offset = None;
    let mut symtab_entry_offset: usize = offset;
    let mut symtab_entries: Vec<VxWorksSymbolTableEntry> = vec![];

    // Determine the symbol table endianness first
    if let Ok(endianness) = get_symtab_endianness(&file_data[symtab_entry_offset..]) {
        // Loop through all the symbol table entries, until we run out of data or hit an invalid entry
        while is_offset_safe(available_data, symtab_entry_offset, previous_entry_offset) {
            // Parse the symbol table entry
            match parse_symtab_entry(&file_data[symtab_entry_offset..], &endianness) {
                // Break on an invalid entry
                Err(_) => {
                    break;
                }

                // Increment symtab_entry_offset to the offset of the next entry and keep a list of all processed entries
                Ok(entry) => {
                    previous_entry_offset = Some(symtab_entry_offset);
                    symtab_entry_offset += entry.size;
                    symtab_entries.push(entry);
                }
            }
        }
    }

    // Sanity check the number of symbols in the symbol table; there are usualy MANY
    if symtab_entries.len() >= MIN_VALID_ENTRIES {
        result.success = true;
        result.size = Some(symtab_entry_offset - offset);

        // This is not a drill!
        if output_directory.is_some() {
            let chroot = Chroot::new(output_directory);

            // Convert symbol table entires to JSON
            match serde_json::to_string_pretty(&symtab_entries) {
                // This should never happen...
                Err(e) => {
                    panic!("Failed to convert VxWorks symbol table to JSON: {}", e);
                }

                // Write JSON to file
                Ok(symtab_json) => {
                    result.success =
                        chroot.create_file(OUTFILE_NAME, &symtab_json.clone().into_bytes());
                }
            }
        }
    }

    result
}
