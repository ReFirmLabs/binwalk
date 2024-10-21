use crate::common::is_offset_safe;
use crate::extractors::common::{
    Chroot, ExtractionError, ExtractionResult, Extractor, ExtractorType,
};
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
    block_device: bool,
    character_device: bool,
    fifo: bool,
    socket: bool,
    symlink: bool,
    symlink_target: String,
    device_major: usize,
    device_minor: usize,
    children: Vec<RomFSEntry>,
}

/// Defines the internal extractor function for extracting RomFS file systems */
pub fn romfs_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_romfs),
        ..Default::default()
    }
}

/// Internal RomFS extractor
pub fn extract_romfs(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Parse the RomFS header
    if let Ok(romfs_header) = parse_romfs_header(&file_data[offset..]) {
        // Calculate start and end offsets of RomFS image
        let romfs_data_start: usize = offset;
        let romfs_data_end: usize = romfs_data_start + romfs_header.image_size;

        // Sanity check reported image size and get the romfs data
        if let Some(romfs_data) = file_data.get(romfs_data_start..romfs_data_end) {
            // Process the RomFS file entries
            if let Ok(root_entries) = process_romfs_entries(romfs_data, romfs_header.header_size) {
                // We expect at least one file entry in the root of the RomFS image
                if !root_entries.is_empty() {
                    // Everything looks good
                    result.success = true;
                    result.size = Some(romfs_header.image_size);

                    // Do extraction, if an output directory was provided
                    if output_directory.is_some() {
                        let mut file_count: usize = 0;
                        let root_parent = "".to_string();

                        // RomFS files will be extracted to a sub-directory under the specified
                        // extraction directory whose name is the RomFS volume name.
                        let chroot = Chroot::new(output_directory);
                        let romfs_chroot_dir = chroot.chrooted_path(&romfs_header.volume_name);

                        // Create the romfs output directory, ensuring that it is contained inside the specified extraction directory
                        if chroot.create_directory(&romfs_chroot_dir) {
                            // Extract RomFS contents
                            file_count = extract_romfs_entries(
                                romfs_data,
                                &root_entries,
                                &root_parent,
                                &romfs_chroot_dir,
                            );
                        }

                        // If no files were extracted, extraction was a failure
                        if file_count == 0 {
                            result.success = false;
                        }
                    }
                }
            }
        }
    }

    result
}

// Recursively processes all RomFS file entries and their children, and returns a list of RomFSEntry structures
fn process_romfs_entries(
    romfs_data: &[u8],
    offset: usize,
) -> Result<Vec<RomFSEntry>, ExtractionError> {
    let mut previous_file_offset = None;
    let mut file_entries: Vec<RomFSEntry> = vec![];
    let mut processed_entries: Vec<usize> = vec![];
    let ignore_file_names: Vec<String> = vec![".".to_string(), "..".to_string()];

    // Total available data
    let available_data = romfs_data.len();

    // File data starts immediately after the image header; the offset passed in should be the end of the header
    let mut file_offset: usize = offset;

    /*
     * Sanity check the available file data against the offset of the next file entry.
     * The file offset for the next file entry will be 0 when we've reached the end of the entry list.
     */
    while file_offset != 0 && is_offset_safe(available_data, file_offset, previous_file_offset) {
        // Sanity check, no two entries should exist at the same offset, if so, infinite recursion could ensue
        if processed_entries.contains(&file_offset) {
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
            file_entry.block_device = file_header.block_device;
            file_entry.character_device = file_header.character_device;
            file_entry.fifo = file_header.fifo;
            file_entry.socket = file_header.socket;

            // Make file_entry.offset an offset relative to the beginning of the RomFS image
            file_entry.offset = file_offset + file_header.data_offset;

            // Sanity check the file data offset and size fields
            if (file_entry.offset + file_entry.size) > romfs_data.len() {
                warn!("Invalid offset/size specified for file {}", file_entry.name);
                return Err(ExtractionError);
            }

            // Don't do anything special for '.' or '..' directory entries
            if !ignore_file_names.contains(&file_entry.name) {
                // Symlinks need their target paths
                if file_entry.symlink {
                    if let Some(symlink_bytes) =
                        romfs_data.get(file_entry.offset..file_entry.offset + file_entry.size)
                    {
                        match String::from_utf8(symlink_bytes.to_vec()) {
                            Err(e) => {
                                warn!("Failed to convert symlink target path to string: {}", e);
                                return Err(ExtractionError);
                            }
                            Ok(path) => {
                                file_entry.symlink_target = path.clone();
                            }
                        }
                    } else {
                        break;
                    }
                // Device files have their major/minor numbers encoded into the info field
                } else if file_entry.block_device || file_entry.character_device {
                    file_entry.device_minor = file_entry.info & 0xFFFF;
                    file_entry.device_major = (file_entry.info >> 16) & 0xFFFF;
                }

                // Directories have children; process them
                if file_entry.directory {
                    match process_romfs_entries(romfs_data, file_entry.info) {
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
            previous_file_offset = Some(file_offset);
            file_offset = file_header.next_header_offset;
        } else {
            // File entry header parsing failed, gtfo
            break;
        }
    }

    Ok(file_entries)
}

// Recursively extract all RomFS entries, returns the number of extracted files/directories
fn extract_romfs_entries(
    romfs_data: &[u8],
    romfs_files: &Vec<RomFSEntry>,
    parent_directory: &String,
    chroot_directory: &String,
) -> usize {
    let mut file_count: usize = 0;

    let chroot = Chroot::new(Some(chroot_directory));

    for file_entry in romfs_files {
        let extraction_success: bool;
        let file_path = chroot.safe_path_join(parent_directory, &file_entry.name);

        if file_entry.directory {
            extraction_success = chroot.create_directory(&file_path);
        } else if file_entry.regular {
            extraction_success =
                chroot.carve_file(&file_path, romfs_data, file_entry.offset, file_entry.size);
        } else if file_entry.symlink {
            extraction_success = chroot.create_symlink(&file_path, &file_entry.symlink_target);
        } else if file_entry.fifo {
            extraction_success = chroot.create_fifo(&file_path);
        } else if file_entry.socket {
            extraction_success = chroot.create_socket(&file_path);
        } else if file_entry.block_device {
            extraction_success = chroot.create_block_device(
                &file_path,
                file_entry.device_major,
                file_entry.device_minor,
            );
        } else if file_entry.character_device {
            extraction_success = chroot.create_character_device(
                &file_path,
                file_entry.device_major,
                file_entry.device_minor,
            );
        } else {
            continue;
        }

        if extraction_success {
            file_count += 1;

            // Extract the children of a directory
            if file_entry.directory && !file_entry.children.is_empty() {
                file_count += extract_romfs_entries(
                    romfs_data,
                    &file_entry.children,
                    &file_path,
                    chroot_directory,
                );
            }

            // Make executable files executable
            if file_entry.regular && file_entry.executable {
                chroot.make_executable(&file_path);
            }
        } else {
            warn!("Failed to extract RomFS file {}", file_path);
        }
    }

    // Return the number of files extracted
    file_count
}
