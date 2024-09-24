use crate::signatures::common::SignatureResult;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::os::unix;
use std::os::unix::fs::PermissionsExt;
use std::path;
use std::process;
use walkdir::WalkDir;

/* This contstant in command line arguments will be replaced with the path to the input file */
pub const SOURCE_FILE_PLACEHOLDER: &str = "%e";

#[derive(Debug, Clone)]
pub struct ExtractionError;

/*
 * Built-in internal extractors must provide a function conforming to this definition.
 * Arguments: file_data, offset, output_directory.
 */
pub type InternalExtractor = fn(&Vec<u8>, usize, Option<&String>) -> ExtractionResult;

#[derive(Debug, Default, Clone, Eq, PartialEq, Ord, PartialOrd)]
pub enum ExtractorType {
    External(String),
    Internal(InternalExtractor),
    #[default]
    None,
}

/*
 * Describes an extractor.
 */
#[derive(Debug, Clone, Default, PartialEq, Eq, PartialOrd, Ord)]
pub struct Extractor {
    // External command or internal function to execute
    pub utility: ExtractorType,
    // File extension expected by an external command
    pub extension: String,
    // Arguments to pass to the external command
    pub arguments: Vec<String>,
    // A list of successful exit codes for the external command
    pub exit_codes: Vec<i32>,
    // Set to true to disable recursion into this extractor's extracted files
    pub do_not_recurse: bool,
}

/*
 * Stores information about a completed extraction.
 * When constructing this structure, only the `size` and `success` fields should be populated;
 * the others are automatically populated (see: execute(), below).
 */
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExtractionResult {
    // Size of the data consumed during extraction, if known
    pub size: Option<usize>,
    // Extractor success status
    pub success: bool,
    // Extractor name, automatically populated by execute(), below
    pub extractor: String,
    // Set to true if the corresponding Extractor definition has it set to true
    // WARNING: this value must be defined in the extractor definition, as that
    // will override this value (see execute(), below).
    pub do_not_recurse: bool,
    // The output directory where the extractor dropped its files, automatically populated by execute(), below
    pub output_directory: String,
}

/*
 * Stores information about external extractor processes.
 */
#[derive(Debug)]
pub struct ProcInfo {
    pub child: process::Child,
    pub exit_codes: Vec<i32>,
    pub carved_file: String,
}

/*
 * Joins two paths, ensuring that the file_path does not traverse outside of the chroot directory.
 */
pub fn safe_path_join(chroot_directory: &String, file_path: &String) -> String {
    const DIR_TRAVERSAL: &str = "..";

    let mut exclude_indicies: Vec<usize> = vec![];
    let mut sanitized_path: String = chroot_directory.clone();

    // Split the file path on '/'
    let path_parts: Vec<&str> = file_path.split(path::MAIN_SEPARATOR).collect();

    // Loop through each part of the file path
    for i in 0..path_parts.len() {
        // If this part of the path is '..', don't include it in the final sanitized path
        if path_parts[i] == DIR_TRAVERSAL {
            exclude_indicies.push(i);
            if i > 0 {
                // Walk backwards through the path parts until a non-excluded part is found, then mark that part for exclusion as well
                let mut j = i - 1;
                while j > 0 && exclude_indicies.contains(&j) {
                    j -= 1;
                }
                exclude_indicies.push(j);
            }
        // If this part of the path is an empty string, don't include that either (happens if the original file path has '//' in it)
        } else if path_parts[i].len() == 0 {
            exclude_indicies.push(i);
        }
    }

    // Append each non-excluded part of the file path to the specified chroot directory path
    for i in 0..path_parts.len() {
        if exclude_indicies.contains(&i) == false {
            sanitized_path = format!(
                "{}{}{}",
                sanitized_path,
                path::MAIN_SEPARATOR,
                path_parts[i]
            );
        }
    }

    return sanitized_path;
}

/*
 * Creates a regular file and writes the provided data to it.
 */
pub fn create_file(file_path: &String, data: &[u8], start: usize, size: usize) -> bool {
    let end: usize = start + size;

    if path::Path::new(file_path).exists() == false {
        if data.len() >= end {
            match fs::write(file_path, data[start..end].to_vec()) {
                Ok(_) => {
                    return true;
                }
                Err(e) => {
                    error!("Failed to write data to {}: {}", file_path, e);
                }
            }
        } else {
            error!(
                "Failed to create file {}: offset/size provided exceeds available data",
                file_path
            );
        }
    } else {
        error!("Failed to create file {}: path already exists", file_path);
    }

    return false;
}

/*
 * Returns true if the file path is a symlink.
 */
pub fn is_symlink(file_path: &String) -> bool {
    if let Ok(metadata) = fs::symlink_metadata(file_path) {
        return metadata.file_type().is_symlink();
    }

    return false;
}

/*
 * Append the provided data to the specified file path.
 */
pub fn append_to_file(file_path: &String, data: &[u8]) -> bool {
    if is_symlink(file_path) == false {
        match fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)
        {
            Err(e) => {
                error!("Failed to open file '{}' for appending: {}", file_path, e);
            }
            Ok(mut fp) => match fp.write(data) {
                Err(e) => {
                    error!("Failed to append to file '{}': {}", file_path, e);
                }
                Ok(_) => {
                    return true;
                }
            },
        }
    } else {
        error!("Attempted to append data to a symlink: {}", file_path);
    }

    return false;
}

/*
 * Equivalent to mkdir -p
 */
pub fn create_directory(dir_path: &String) -> bool {
    match fs::create_dir_all(dir_path) {
        Ok(_) => {
            return true;
        }
        Err(e) => {
            error!("Failed to create output directory {}: {}", dir_path, e);
        }
    }

    return false;
}

/*
 * Make a file executable.
 * Other ownership/permissions are generally not set by extractors, as they can lead to
 * extracted files that cannot be opened and analyzed.
 */
pub fn make_executable(file_path: &String) -> bool {
    // Make the file globally executable
    const UNIX_EXEC_FLAG: u32 = 1;

    match fs::metadata(file_path) {
        Err(e) => {
            error!("Failed to get permissions for file {}: {}", file_path, e);
        }
        Ok(metadata) => {
            let mut permissions = metadata.permissions();
            permissions.set_mode(permissions.mode() | UNIX_EXEC_FLAG);

            match fs::set_permissions(file_path, permissions) {
                Err(e) => {
                    error!("Failed to set permissions for file {}: {}", file_path, e);
                }
                Ok(_) => {
                    return true;
                }
            }
        }
    }

    return false;
}

/*
 * Creates a symlink named symlink which points to target.
 */
pub fn create_symlink(symlink: &String, target: &String) -> bool {
    let target_path = path::Path::new(target);
    let symlink_path = path::Path::new(symlink);
    match unix::fs::symlink(&target_path, &symlink_path) {
        Ok(_) => {
            return true;
        }
        Err(e) => {
            error!(
                "Failed to created symlink from {} -> {}: {}",
                symlink, target, e
            );
            return false;
        }
    }
}

/*
 * Recursively walks a given directory and returns a list of regular non-zero size files in the given directory path.
 */
pub fn get_extracted_files(directory: &String) -> Vec<String> {
    let mut regular_files: Vec<String> = vec![];

    for entry in WalkDir::new(directory).into_iter() {
        match entry {
            Err(_e) => continue,
            Ok(entry) => {
                let entry_path = entry.path();
                // Query file metadata *without* following symlinks
                match fs::symlink_metadata(entry_path) {
                    Err(_e) => continue,
                    Ok(md) => {
                        // Only interested in non-empty, regular files
                        if md.is_file() && md.len() > 0 {
                            regular_files.push(entry_path.to_str().unwrap().to_string());
                        }
                    }
                }
            }
        }
    }

    return regular_files;
}

/*
 * Executes an extractor for the provided SignatureResult.
 */
pub fn execute(
    file_data: &Vec<u8>,
    file_path: &String,
    signature: &SignatureResult,
    extractor: &Option<Extractor>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Create an output directory for the extraction
    if let Ok(output_directory) = create_output_directory(file_path, signature.offset) {
        // Make sure a defalut extractor was actually defined (this function should not be called if signature.extractor is None)
        match &extractor {
            None => {
                error!(
                    "Attempted to extract {} data, but no extractor is defined!",
                    signature.name
                );
            }

            Some(default_extractor) => {
                let extractor_definition: Extractor;

                // If the signature result specified a preferred extractor, use that instead of the default signature extractor
                if let Some(preferred_extractor) = &signature.preferred_extractor {
                    extractor_definition = preferred_extractor.clone();
                } else {
                    extractor_definition = default_extractor.clone();
                }

                // Decide how to execute the extractor depending on the extractor type
                match &extractor_definition.utility {
                    ExtractorType::None => {
                        panic!("An extractor of type None is invalid!");
                    }

                    ExtractorType::Internal(func) => {
                        // Run the internal extractor function
                        result = func(file_data, signature.offset, Some(&output_directory));
                        // Set the extractor name to "<signature name>_built_in"
                        result.extractor = format!("{}_built_in", signature.name);
                    }

                    ExtractorType::External(cmd) => {
                        // Spawn the external extractor command
                        match spawn(
                            file_data,
                            file_path,
                            &output_directory,
                            signature,
                            extractor_definition.clone(),
                        ) {
                            Err(e) => {
                                error!(
                                    "Failed to spawn external extractor for '{}' signature: {}",
                                    signature.name, e
                                );
                            }

                            Ok(proc_info) => {
                                // Wait for the external process to exit
                                match proc_wait(proc_info) {
                                    Err(_) => {
                                        warn!("External extractor failed!");
                                    }
                                    Ok(ext_result) => {
                                        result = ext_result;
                                        // Set the extractor name to the name of the extraction utility
                                        result.extractor = cmd.to_string();
                                    }
                                }
                            }
                        }
                    }
                }

                // Populate these ExtractionResult fields automatically for all extractors
                result.output_directory = output_directory.clone();
                result.do_not_recurse = extractor_definition.do_not_recurse;

                // If the extractor reported success, make sure it extracted something other than just an empty file
                if result.success == true {
                    if was_something_extracted(&result.output_directory) == false {
                        result.success = false;
                        warn!("Extractor exited successfully, but no data was extracted");
                    }
                }
            }
        }

        // Clean up extractor's output directory if extraction failed
        if result.success == false {
            if let Err(e) = fs::remove_dir_all(&output_directory) {
                warn!(
                    "Failed to clean up extraction directory {} after extraction failure: {}",
                    output_directory, e
                );
            }
        }
    }

    return result;
}

/*
 * Spawn an external extractor process.
 */
fn spawn(
    file_data: &Vec<u8>,
    file_path: &String,
    output_directory: &String,
    signature: &SignatureResult,
    mut extractor: Extractor,
) -> Result<ProcInfo, std::io::Error> {
    let command: String;

    // This function *only* handles execution of external extraction utilities; internal extractors must be invoked directly
    match &extractor.utility {
        ExtractorType::External(cmd) => command = cmd.clone(),
        ExtractorType::Internal(_ext) => {
            panic!("Tried to run an internal extractor as an external command!")
        }
        ExtractorType::None => panic!("An extractor command was defined, but is set to None!"),
    }

    // Carved file path will be <output directory>/<signature.name>_<hex offset>.<extractor.extension>
    let carved_file = format!(
        "{}{}{}_{:X}.{}",
        output_directory,
        path::MAIN_SEPARATOR,
        signature.name,
        signature.offset,
        extractor.extension
    );
    info!(
        "Carving data from {} {:#X}..{:#X} to {}",
        file_path,
        signature.offset,
        signature.offset + signature.size,
        carved_file
    );

    // If the entirety of the source file is this one file type, no need to carve a copy of it, just create a symlink
    if signature.offset == 0 && signature.size == file_data.len() {
        if create_symlink(&carved_file, &file_path) == false {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Failed to create carved file symlink",
            ));
        }
    } else {
        // Copy file data to carved file path
        if create_file(&carved_file, file_data, signature.offset, signature.size) == false {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Failed to carve data to disk",
            ));
        }
    }

    // Replace all "%e" command arguments with the path to the carved file
    for i in 0..extractor.arguments.len() {
        if extractor.arguments[i] == SOURCE_FILE_PLACEHOLDER {
            extractor.arguments[i] = carved_file.clone();
        }
    }

    info!("Spawning process {} {:?}", command, extractor.arguments);
    match process::Command::new(&command)
        .args(&extractor.arguments)
        .stdout(process::Stdio::null())
        .stderr(process::Stdio::null())
        .current_dir(&output_directory)
        .spawn()
    {
        Err(e) => {
            error!(
                "Failed to execute command {}{:?}: {}",
                command, extractor.arguments, e
            );
            return Err(e);
        }

        Ok(child) => {
            // If the process was spawned successfully, return some information about the process
            let proc_info = ProcInfo {
                child: child,
                carved_file: carved_file.clone(),
                exit_codes: extractor.exit_codes,
            };

            return Ok(proc_info);
        }
    }
}

/*
 * Waits for an extraction process to complete.
 * Returns ExtractionError if the extractor was prematurely terminated, else returns an ExtractionResult.
 */
fn proc_wait(mut worker_info: ProcInfo) -> Result<ExtractionResult, ExtractionError> {
    // The standard exit success value is 0
    const EXIT_SUCCESS: i32 = 0;

    // Block until child process has terminated
    match worker_info.child.wait() {
        // Child was terminated from an external signal, status unknown, assume failure but do nothing else
        Err(e) => {
            error!("Failed to retreive child process status: {}", e);
            return Err(ExtractionError);
        }

        // Child terminated with an exit status
        Ok(status) => {
            // Assume failure until proven otherwise
            let mut extraction_success: bool = false;

            // Clean up the carved file used as input to the extractor
            debug!("Deleting carved file {}", worker_info.carved_file);
            if let Err(e) = fs::remove_file(worker_info.carved_file.clone()) {
                warn!(
                    "Failed to remove carved file '{}': {}",
                    worker_info.carved_file, e
                );
            };

            // Check the extractor's exit status
            match status.code() {
                None => {
                    extraction_success = false;
                }

                Some(code) => {
                    // Make sure the extractor's exit code is an expected one
                    if code == EXIT_SUCCESS || worker_info.exit_codes.contains(&code) {
                        extraction_success = true;
                    } else {
                        warn!("Child process exited with unexpected code: {}", code);
                    }
                }
            }

            // Return an ExtractionResult with the appropriate success status
            return Ok(ExtractionResult {
                success: extraction_success,
                ..Default::default()
            });
        }
    }
}

// Create an output directory in which to place extraction results
fn create_output_directory(file_path: &String, offset: usize) -> Result<String, std::io::Error> {
    // Output directory will be: <file_path.extracted/<hex offset>
    let output_directory = format!(
        "{}.extracted{}{:X}",
        file_path,
        path::MAIN_SEPARATOR,
        offset
    );

    // Create the output directory, equivalent of mkdir -p
    if create_directory(&output_directory) == false {
        return Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            "Directory creation failed",
        ));
    }

    return Ok(output_directory);
}

/*
 * Returns true if the size of the provided extractor output directory is greater than zero.
 * Note that any intermediate/carved files must be deleted *before* calling this function.
 */
fn was_something_extracted(output_directory: &String) -> bool {
    let output_directory_path = path::Path::new(output_directory);
    debug!("Checking output directory {} for results", output_directory);

    // Walk the output directory looking for something, anything, that isn't an empty file
    for entry in WalkDir::new(output_directory).into_iter() {
        match entry {
            Err(e) => {
                warn!("Failed to retrieve output directory entry: {}", e);
                continue;
            }
            Ok(entry) => {
                // Don't include the base output directory path itself
                if entry.path() == output_directory_path {
                    continue;
                }

                debug!("Found output file {}", entry.path().display());

                match fs::symlink_metadata(entry.path()) {
                    Err(_e) => continue,
                    Ok(md) => {
                        if md.len() > 0 {
                            return true;
                        }
                    }
                }
            }
        }
    }

    return false;
}
