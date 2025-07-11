use crate::common::is_offset_safe;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::csman::{CSManEntry, parse_csman_entry, parse_csman_header};
use miniz_oxide::inflate;
use std::collections::HashMap;

/// Defines the internal extractor function for CSMan DAT files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::csman::csman_extractor;
///
/// match csman_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn csman_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_csman_dat),
        ..Default::default()
    }
}

/// Validate and extract CSMan DAT file entries
pub fn extract_csman_dat(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    const COMPRESSED_HEADER_SIZE: usize = 2;

    // Return value
    let mut result = ExtractionResult {
        ..Default::default()
    };

    let mut csman_entries: Vec<CSManEntry> = Vec::new();

    // Parse the CSMAN header
    if let Ok(csman_header) = parse_csman_header(&file_data[offset..]) {
        // Calulate the start and end offsets of the CSMAN entries
        let entries_start: usize = offset + csman_header.header_size;
        let entries_end: usize = entries_start + csman_header.data_size;

        // Get the CSMAN entry data
        if let Some(raw_entry_data) = file_data.get(entries_start..entries_end) {
            let mut entry_data = raw_entry_data.to_vec();

            // If the entries are compressed, decompress it (zlib compression)
            if csman_header.compressed {
                if let Some(compressed_data) = raw_entry_data.get(COMPRESSED_HEADER_SIZE..) {
                    match inflate::decompress_to_vec(compressed_data) {
                        Err(_) => {
                            return result;
                        }
                        Ok(decompressed_data) => {
                            entry_data = decompressed_data.clone();
                        }
                    }
                }
            }

            // Offsets for processing CSMAN entries in entry_data
            let mut next_offset: usize = 0;
            let mut previous_offset = None;
            let available_data: usize = entry_data.len();

            // Loop while there is still data that can be safely parsed
            while is_offset_safe(available_data, next_offset, previous_offset) {
                // Get the next entry's data
                match entry_data.get(next_offset..) {
                    None => {
                        break;
                    }
                    Some(next_entry_data) => {
                        // Parse the next entry
                        match parse_csman_entry(next_entry_data, &csman_header.endianness) {
                            Err(_) => {
                                break;
                            }
                            Ok(entry) => {
                                if entry.eof {
                                    // Last entry should be an EOF marker; an EOF marker should always exist.
                                    // There should be at least one valid entry.
                                    result.success = !csman_entries.is_empty();
                                    break;
                                } else {
                                    // Append this entry to the list of entries and update the offsets to process the next entry
                                    csman_entries.push(entry.clone());
                                    previous_offset = Some(next_offset);
                                    next_offset += entry.size;
                                }
                            }
                        }
                    }
                }
            }

            // If all entries were processed successfully
            if result.success {
                // Update the reported size of data processed
                result.size = Some(csman_header.header_size + csman_header.data_size);

                // If extraction was requested, extract each entry using the entry key as the file name
                if output_directory.is_some() {
                    // All files will be written inside the provided output directory
                    let chroot = Chroot::new(output_directory);

                    // There may be more than one entry with the same key; track the key and how many times it was encountered
                    let mut processed_entries: HashMap<usize, usize> = HashMap::new();

                    // Loop through all entries
                    for entry in csman_entries {
                        // File name is [key value, in ASCII hex].dat
                        let mut file_name = format!("{:08X}.dat", entry.key);

                        // If this key value has already been extracted, file name is [key value, in ASCII hex].dat_[count]
                        if processed_entries.contains_key(&entry.key) {
                            file_name = format!("{}_{}", file_name, processed_entries[&entry.key]);
                            processed_entries.insert(entry.key, processed_entries[&entry.key] + 1);
                        } else {
                            processed_entries.insert(entry.key, 1);
                        }

                        if !chroot.create_file(&file_name, &entry.value) {
                            result.success = false;
                            break;
                        }
                    }
                }
            }
        }
    }

    result
}
