use crate::extractors::common::{
    create_directory, create_file, create_symlink, make_executable, safe_path_join,
};
use crate::extractors::common::{ExtractionError, ExtractionResult, Extractor, ExtractorType};
use crate::structures::romfs::{parse_romfs_file_entry, parse_romfs_header};
use log::warn;

#[derive(Default, Debug, Clone)]
struct RomFSEntry {
    info: usize,
    size: usize,
    name: String,
    offset: usize,
    file_type: usize,
    executable: bool,
    directory: bool,
    regular: bool,
    symlink: bool,
    symlink_target: String,
    children: Vec<RomFSEntry>,
}

/* Defines the internal extractor function for extracting RomFS file systems */
pub fn romfs_extractor() -> Extractor {
    return Extractor {
        utility: ExtractorType::Internal(extract_romfs),
        ..Default::default()
    };
}

/*
 * Main RomFS extraction function.
 */
pub fn extract_romfs(
    file_data: &Vec<u8>,
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    let do_extraction: bool;
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Only perform extraction if an output directory was provided
    match output_directory {
        None => do_extraction = false,
        Some(_) => do_extraction = true,
    }

    // RomFS start is known, size is not...
    let mut romfs_data: &[u8] = &file_data[offset..];

    // Parse the RomFS header
    if let Ok(romfs_header) = parse_romfs_header(romfs_data) {
        // Calculate start and end offsets of RomFS image
        let romfs_data_start: usize = offset;
        let romfs_data_end: usize = romfs_data_start + romfs_header.image_size;

        // Sanity check available file data
        if file_data.len() >= romfs_data_end {
            // Now that the size of the image is known, restrict romfs_data to that size
            romfs_data = &file_data[romfs_data_start..romfs_data_end];

            // Process the RomFS file entries
            if let Ok(root_entries) = process_romfs_entries(romfs_data, romfs_header.header_size) {
                // Everything looks good
                result.success = true;
                result.size = Some(romfs_header.image_size);

                // Do extraction, if an output directory was provided
                if do_extraction {
                    // Extracted files will be placed in the specified output directory, under a sub-directory named after the RomFS volume
                    let extraction_directory: String =
                        safe_path_join(&output_directory.unwrap(), &romfs_header.volume_name);

                    // Do the extraction
                    let file_count =
                        extract_romfs_entries(romfs_data, &root_entries, &extraction_directory);

                    // If no files were extracted, extraction was a failure
                    if file_count == 0 {
                        result.success = false;
                    }
                }
            }
        }
    }

    return result;
}

// Recursively processes all RomFS file entries and their children, and returns a list of RomFSEntry structures
fn process_romfs_entries(
    romfs_data: &[u8],
    offset: usize,
) -> Result<Vec<RomFSEntry>, ExtractionError> {
    let mut file_entries: Vec<RomFSEntry> = vec![];
    let mut processed_entries: Vec<usize> = vec![];
    let ignore_file_names: Vec<String> = vec![".".to_string(), "..".to_string()];

    // File data starts immediately after the image header
    let mut file_offset: usize = offset;

    /*
     * Sanity check the available file data against the offset of the next file entry.
     * The file offset for the next file entry will be 0 when we've reached the end of the entry list.
     */
    while file_offset != 0 && romfs_data.len() > file_offset {
        // Sanity check, no two entries should exist at the same offset, if so, infinite recursion could ensue
        if processed_entries.contains(&file_offset) == true {
            break;
        } else {
            processed_entries.push(file_offset);
        }

        // Parse the next file entry
        if let Ok(file_header) = parse_romfs_file_entry(&romfs_data[file_offset..]) {
            // Instantiate a new RomFSEntry structure
            let mut file_entry = RomFSEntry {
                ..Default::default()
            };

            // Populate basic info
            file_entry.size = file_header.size;
            file_entry.info = file_header.info;
            file_entry.name = file_header.name.clone();
            file_entry.symlink = file_header.symlink;
            file_entry.regular = file_header.regular;
            file_entry.directory = file_header.directory;
            file_entry.file_type = file_header.file_type;
            file_entry.executable = file_header.executable;

            // Make file_entry.offset an offset relative to the beginning of the RomFS image
            file_entry.offset = file_offset + file_header.data_offset;

            // Sanity check the file data offset and size fields
            if (file_entry.offset + file_entry.size) > romfs_data.len() {
                warn!("Invalid offset/size specified for file {}", file_entry.name);
                return Err(ExtractionError);
            }

            // Don't do anything special for '.' or '..' directory entries
            if ignore_file_names.contains(&file_entry.name) == false {
                // Symlinks need their target paths
                if file_entry.symlink == true {
                    match String::from_utf8(
                        romfs_data[file_entry.offset..file_entry.offset + file_entry.size].to_vec(),
                    ) {
                        Err(e) => {
                            warn!("Failed to convert symlink target path to string: {}", e);
                            return Err(ExtractionError);
                        }
                        Ok(path) => {
                            file_entry.symlink_target = path.clone();
                        }
                    }
                }

                // Directories have children; process them
                if file_entry.directory == true {
                    match process_romfs_entries(&romfs_data, file_entry.info) {
                        Err(e) => return Err(e),
                        Ok(children) => file_entry.children = children,
                    }
                }

                // Only add supported file types to the list of file entries
                if file_entry.directory || file_entry.symlink || file_entry.regular {
                    file_entries.push(file_entry);
                }
            }

            // The next file header offset is an offset from the beginning of the RomFS image
            file_offset = file_header.next_header_offset;
        } else {
            // File entry header parsing failed, gtfo
            break;
        }
    }

    return Ok(file_entries);
}

// Recursively extract all RomFS entries, returns the number of extracted files/directories
fn extract_romfs_entries(
    romfs_data: &[u8],
    romfs_files: &Vec<RomFSEntry>,
    output_directory: &String,
) -> usize {
    let mut file_count: usize = 0;

    for file_entry in romfs_files {
        let extraction_success: bool;
        let file_path = safe_path_join(output_directory, &file_entry.name);

        if file_entry.directory {
            extraction_success = create_directory(&file_path);
        } else if file_entry.symlink {
            extraction_success = create_symlink(&file_path, &file_entry.symlink_target);
        } else if file_entry.regular {
            extraction_success =
                create_file(&file_path, romfs_data, file_entry.offset, file_entry.size);
        } else {
            // This should never happen, panic if it does
            panic!("RomFS entry is an unsupported type: {:?}", file_entry);
        }

        if extraction_success == true {
            file_count += 1;

            // Extract the children of a directory
            if file_entry.directory == true && file_entry.children.len() > 0 {
                file_count += extract_romfs_entries(romfs_data, &file_entry.children, &file_path);
            }

            // Make executable files executable
            if file_entry.regular == true && file_entry.executable == true {
                make_executable(&file_path);
            }
        } else {
            warn!("Failed to extract RomFS file {}", file_path);
        }
    }

    // Return the number of files extracted
    return file_count;
}
