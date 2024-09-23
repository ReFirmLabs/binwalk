use crate::extractors::common::{create_file, safe_path_join};
use crate::extractors::common::{ExtractionResult, Extractor, ExtractorType};
use crate::structures::vxworks::{
    get_symtab_endianness, parse_symtab_entry, VxWorksSymbolTableEntry,
};
use serde_json;

pub fn vxworks_symtab_extractor() -> Extractor {
    return Extractor {
        do_not_recurse: true,
        utility: ExtractorType::Internal(extract_symbol_table),
        ..Default::default()
    };
}

pub fn extract_symbol_table(
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const MIN_VALID_ENTRIES: usize = 250;
    const OUTFILE_NAME: &str = "symtab.json";

    let dry_run: bool;
    let output_file_path: String;
    let mut result = ExtractionResult {
        ..Default::default()
    };

    let mut symtab_entry_offset: usize = offset;
    let mut symtab_entries: Vec<VxWorksSymbolTableEntry> = vec![];

    // Check if this is just a dry-run or a full extraction
    match output_directory {
        Some(dir) => {
            dry_run = false;
            output_file_path = safe_path_join(dir, &OUTFILE_NAME.to_string());
        }
        None => {
            dry_run = true;
            output_file_path = "".to_string();
        }
    }

    // Determine the symbol table endianness first
    if let Ok(endianness) = get_symtab_endianness(&file_data[symtab_entry_offset..]) {
        // Loop through all the symbol table entries, until we run out of data or hit an invalid entry
        while symtab_entry_offset < file_data.len() {
            // Parse the symbol table entry
            match parse_symtab_entry(&file_data[symtab_entry_offset..], &endianness) {
                // Break on an invalid entry
                Err(_) => {
                    break;
                }

                // Increment symtab_entry_offset to the offset of the next entry and keep a list of all processed entries
                Ok(entry) => {
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
        if dry_run == false {
            // Convert symbol table entires to JSON
            match serde_json::to_string_pretty(&symtab_entries) {
                // This should never happen...
                Err(e) => {
                    panic!("Failed to convert VxWorks symbol table to JSON: {}", e);
                }

                // Write JSON to file
                Ok(symtab_json) => {
                    result.success = create_file(
                        &output_file_path,
                        &symtab_json.clone().into_bytes(),
                        0,
                        symtab_json.len(),
                    );
                }
            }
        }
    }

    return result;
}
