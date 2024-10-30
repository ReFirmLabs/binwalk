//! Primary Binwalk interface.

use aho_corasick::AhoCorasick;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path;
use uuid::Uuid;

#[cfg(windows)]
use std::os::windows;

#[cfg(unix)]
use std::os::unix;

use crate::common::{is_offset_safe, read_file};
use crate::extractors;
use crate::magic;
use crate::signatures;

/// Returned on initialization error
#[derive(Debug, Default, Clone)]
pub struct BinwalkError;

/// Analysis results returned by Binwalk::analyze
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct AnalysisResults {
    /// Path to the file that was analyzed
    pub file_path: String,
    /// File signature results, as returned by Binwalk::scan
    pub file_map: Vec<signatures::common::SignatureResult>,
    /// File extraction results, as returned by Binwalk::extract.
    /// HashMap key is the corresponding SignatureResult.id value in `file_map`.
    pub extractions: HashMap<String, extractors::common::ExtractionResult>,
}

/// Analyze files / memory for file signatures
///
/// ## Example
///
/// ```
/// use binwalk::Binwalk;
///
/// let target_file = "/bin/ls";
/// let data_to_scan = std::fs::read(target_file).expect("Unable to read file");
///
/// let binwalker = Binwalk::new();
///
/// let signature_results = binwalker.scan(&data_to_scan);
///
/// for result in &signature_results {
///     println!("Found '{}' at offset {:#X}", result.description, result.offset);
/// }
/// ```
#[derive(Debug, Default, Clone)]
pub struct Binwalk {
    /// Count of all signatures (short and regular)
    pub signature_count: usize,
    /// The base file requested for analysis
    pub base_target_file: String,
    /// The base output directory for extracted files
    pub base_output_directory: String,
    /// A list of signatures that must start at offset 0
    pub short_signatures: Vec<signatures::common::Signature>,
    /// A list of magic bytes to search for throughout the entire file
    pub patterns: Vec<Vec<u8>>,
    /// Maps patterns to their corresponding signature
    pub pattern_signature_table: HashMap<usize, signatures::common::Signature>,
    /// Maps signatures to their corresponding extractors
    pub extractor_lookup_table: HashMap<String, Option<extractors::common::Extractor>>,
}

impl Binwalk {
    /// Create a new Binwalk instance with all default values.
    /// Equivalent to `Binwalk::configure(None, None, None, None, None, false)`.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::Binwalk;
    ///
    /// let binwalker = Binwalk::new();
    /// ```
    #[allow(dead_code)]
    pub fn new() -> Binwalk {
        Binwalk::configure(None, None, None, None, None, false).unwrap()
    }

    /// Create a new Binwalk instance.
    ///
    /// If `target_file_name` and `output_directory` are specified, the `output_directory` will be created if it does not
    /// already exist, and a symlink to `target_file_name` will be placed inside the `output_directory`. The path to this
    /// symlink is placed in `Binwalk.base_target_file`.
    ///
    /// The `include` and `exclude` arguments specify include and exclude signature filters. The String values contained
    /// in these arguments must match the `Signature.name` values defined in magic.rs.
    ///
    /// Additional user-defined signatures may be provided via the `signatures` argument.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_binwalk_rs_102_0() -> Result<binwalk::Binwalk, binwalk::BinwalkError> {
    /// use binwalk::Binwalk;
    ///
    /// // Don't scan for these file signatures
    /// let exclude_filters: Vec<String> = vec!["jpeg".to_string(), "png".to_string()];
    ///
    /// let binwalker = Binwalk::configure(None,
    ///                                    None,
    ///                                    None,
    ///                                    Some(exclude_filters),
    ///                                    None,
    ///                                    false)?;
    /// # Ok(binwalker)
    /// # } _doctest_main_src_binwalk_rs_102_0(); }
    /// ```
    pub fn configure(
        target_file_name: Option<String>,
        output_directory: Option<String>,
        include: Option<Vec<String>>,
        exclude: Option<Vec<String>>,
        signatures: Option<Vec<signatures::common::Signature>>,
        full_search: bool,
    ) -> Result<Binwalk, BinwalkError> {
        let mut new_instance = Binwalk {
            ..Default::default()
        };

        // Target file is optional, especially if being called via the library
        if let Some(target_file) = target_file_name {
            // Set the target file path, make it an absolute path
            match path::absolute(&target_file) {
                Err(_) => {
                    return Err(BinwalkError);
                }
                Ok(abspath) => {
                    new_instance.base_target_file = abspath.display().to_string();
                }
            }

            // If an output extraction directory was also specified, initialize it
            if let Some(extraction_directory) = output_directory {
                // Make the extraction directory an absolute path
                match path::absolute(&extraction_directory) {
                    Err(_) => {
                        return Err(BinwalkError);
                    }
                    Ok(abspath) => {
                        new_instance.base_output_directory = abspath.display().to_string();
                    }
                }

                // Initialize the extraction directory. This will create the directory if it
                // does not exist, and create a symlink inside the directory that points to
                // the specified target file.
                match init_extraction_directory(
                    &new_instance.base_target_file,
                    &new_instance.base_output_directory,
                ) {
                    Err(_) => {
                        return Err(BinwalkError);
                    }
                    Ok(new_target_file_path) => {
                        // This is the new base target path (a symlink inside the extraction directory)
                        new_instance.base_target_file = new_target_file_path.clone();
                    }
                }
            }
        }

        // Load all internal signature patterns
        let mut signature_patterns = magic::patterns();

        // Include any user-defined signature patterns
        if let Some(user_defined_signature_patterns) = signatures {
            signature_patterns.extend(user_defined_signature_patterns);
        }

        // Load magic signatures
        for signature in signature_patterns.clone() {
            // Check if this signature should be included
            if !include_signature(&signature, &include, &exclude) {
                continue;
            }

            // Keep a count of total unique signatures that are supported
            new_instance.signature_count += 1;

            // Create a lookup table which associates each signature to its respective extractor
            new_instance
                .extractor_lookup_table
                .insert(signature.name.clone(), signature.extractor.clone());

            // Each signature may have multiple magic bytes associated with it
            for pattern in signature.magic.clone() {
                if signature.short && !full_search {
                    // These are short patterns, and should only be searched for at the very beginning of a file
                    new_instance.short_signatures.push(signature.clone());
                } else {
                    /*
                     * Need to keep a mapping of the pattern index and its associated signature
                     * so that when a match is found it can be resolved back to the signature from
                     * which it came.
                     */
                    new_instance
                        .pattern_signature_table
                        .insert(new_instance.patterns.len(), signature.clone());

                    // Add these magic bytes to the list of patterns
                    new_instance.patterns.push(pattern.to_vec());
                }
            }
        }

        Ok(new_instance)
    }

    /// Scan a file for magic signatures.
    /// Returns a list of validated magic signatures representing the known contents of the file.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::Binwalk;
    ///
    /// let target_file = "/bin/ls";
    /// let data_to_scan = std::fs::read(target_file).expect("Unable to read file");
    ///
    /// let binwalker = Binwalk::new();
    ///
    /// let signature_results = binwalker.scan(&data_to_scan);
    ///
    /// for result in &signature_results {
    ///     println!("{:#X}  {}", result.offset, result.description);
    /// }
    ///
    /// assert!(signature_results.len() > 0);
    /// ```
    pub fn scan(&self, file_data: &[u8]) -> Vec<signatures::common::SignatureResult> {
        const FILE_START_OFFSET: usize = 0;

        let mut index_adjustment: usize = 0;
        let mut next_valid_offset: usize = 0;
        let mut previous_valid_offset = None;

        let available_data = file_data.len();

        // A list of identified signatures, representing a "map" of the file data
        let mut file_map: Vec<signatures::common::SignatureResult> = vec![];

        /*
         * Check beginning of file for short signatures.
         * These signatures are only valid if they occur at the very beginning of a file.
         * This is typically because the signatures are very short and they are likely
         * to occur randomly throughout the file, so this prevents having to validate many
         * false positve matches.
         */
        for signature in &self.short_signatures {
            for magic in signature.magic.clone() {
                let magic_start = FILE_START_OFFSET + signature.magic_offset;
                let magic_end = magic_start + magic.len();

                if file_data.len() > magic_end && file_data[magic_start..magic_end] == magic {
                    debug!(
                        "Found {} short magic match at offset {:#X}",
                        signature.description, magic_start
                    );

                    if let Ok(mut signature_result) = (signature.parser)(file_data, magic_start) {
                        // Auto populate some signature result fields
                        signature_result_auto_populate(&mut signature_result, signature);

                        // Add this signature to the file map
                        file_map.push(signature_result.clone());
                        info!(
                            "Found valid {} short signature at offset {:#X}",
                            signature_result.name, FILE_START_OFFSET
                        );

                        // Only update the next_valid_offset if confidence is high; these are, after all, short signatures
                        if signature_result.confidence >= signatures::common::CONFIDENCE_HIGH {
                            next_valid_offset = signature_result.offset + signature_result.size;
                        }

                        // Only one signature can match at fixed offset 0
                        break;
                    } else {
                        debug!(
                            "{} short signature match at offset {:#X} is invalid",
                            signature.description, FILE_START_OFFSET
                        );
                    }
                }
            }
        }

        /*
         * Same pattern matching algorithm used by fgrep.
         * This will search for all magic byte patterns in the file data, all at once.
         * https://en.wikipedia.org/wiki/Aho–Corasick_algorithm
         */
        let grep = AhoCorasick::new(self.patterns.clone()).unwrap();

        debug!("Running Aho-Corasick scan");

        /*
         * Outer loop wrapper for AhoCorasick scan loop. This will loop until:
         *
         *  1) next_valid_offset exceeds available_data
         *  2) previous_valid_offset <= next_valid_offset
         */
        while is_offset_safe(available_data, next_valid_offset, previous_valid_offset) {
            // Update the previous valid offset in praparation for the next loop iteration
            previous_valid_offset = Some(next_valid_offset);

            debug!("Continuing scan from offset {:#X}", next_valid_offset);

            /*
             * Run a new AhoCorasick scan starting at the next valid offset in the file data.
             * This will loop until:
             *
             *  1) All data has been exhausted, in which case previous_valid_offset and next_valid_offset
             *     will be identical, causing the outer while loop to break.
             *  2) A valid signature with a defined size is found, in which case next_valid_offset will
             *     be updated to point the end of the valid signature data, causing a new AhoCorasick
             *     scan to start at the new next_valid_offset file location.
             */
            for magic_match in grep.find_overlapping_iter(&file_data[next_valid_offset..]) {
                // Get the location of the magic bytes inside the file data
                let magic_offset: usize = next_valid_offset + magic_match.start();

                // Get the signature associated with this magic signature
                let magic_pattern_index: usize = magic_match.pattern().as_usize();
                let signature: signatures::common::Signature = self
                    .pattern_signature_table
                    .get(&magic_pattern_index)
                    .unwrap()
                    .clone();

                debug!(
                    "Found {} magic match at offset {:#X}",
                    signature.description, magic_offset
                );

                /*
                 * Invoke the signature parser to parse and validate the signature.
                 * An error indicates a false positive match for the signature type.
                 */
                if let Ok(mut signature_result) = (signature.parser)(file_data, magic_offset) {
                    // Calculate the end of this signature's data
                    let signature_end_offset = signature_result.offset + signature_result.size;

                    // Sanity check the reported offset and size vs file size
                    if signature_end_offset > available_data {
                        info!("Signature {} extends beyond EOF; ignoring", signature.name);
                        // Continue inner loop
                        continue;
                    }

                    // Auto populate some signature result fields
                    signature_result_auto_populate(&mut signature_result, &signature);

                    // Add this signature to the file map
                    file_map.push(signature_result.clone());

                    info!(
                        "Found valid {} signature at offset {:#X}",
                        signature_result.name, signature_result.offset
                    );

                    // Only update the next_valid_offset if confidence is at least medium
                    if signature_result.confidence >= signatures::common::CONFIDENCE_MEDIUM {
                        // Only update the next_valid offset if the end of the signature reported the size of its contents
                        if signature_result.size > 0 {
                            // This file's signature has a known size, so there's no need to scan inside this file's data.
                            // Update next_valid_offset to point to the end of this file signature and break out of the
                            // inner loop.
                            next_valid_offset = signature_end_offset;
                            break;
                        }
                    }
                } else {
                    debug!(
                        "{} magic match at offset {:#X} is invalid",
                        signature.description, magic_offset
                    );
                }
            }
        }

        debug!("Aho-Corasick scan found {} magic matches", file_map.len());

        /*
         * A file's magic bytes do not always start at the beginning of a file, meaning that it is possible
         * that the order in which the signatures were found in the file data is not the order in which we
         * want to process/validate the signatures. Each signature's parser function will report the correct
         * starting offset for the signature, so sort the file_map by the SignatureResult.offset value.
         */
        file_map.sort();
        next_valid_offset = 0;

        /*
         * Now that signatures are in the correct order, identify and any overlapping signatures
         * (such as gzip files identified within a tarball archive), signatures with the same reported offset,
         * and any signatures with an invalid reported size (i.e., the size extends beyond the end of available file_data).
         */
        for mut i in 0..file_map.len() {
            // Some entries may have been removed from the file_map list in previous loop iterations; adjust the index accordingly
            i -= index_adjustment;

            // Make sure the file map index is valid
            if file_map.is_empty() || i >= file_map.len() {
                break;
            }

            let this_signature = file_map[i].clone();
            let remaining_available_size = file_data.len() - this_signature.offset;

            // Check if the previous file map entry had the same reported starting offset as this one
            if i > 0 && this_signature.offset == file_map[i - 1].offset {
                // Get the previous signature in the file map
                let previous_signature = file_map[i - 1].clone();

                // If this file map entry and the conflicting entry do not have the same confidence level, default to the one with highest confidence
                if this_signature.confidence != previous_signature.confidence {
                    debug!("Conflicting signatures at offset {:#X}; defaulting to the signature with highest confidence", this_signature.offset);

                    // If this signature is higher confidence, invalidate the previous signature
                    if this_signature.confidence > previous_signature.confidence {
                        file_map.remove(i - 1);
                        index_adjustment += 1;

                    // Else, this signature has a lower confidence; invalidate this signature and continue to the next signature in the list
                    } else {
                        file_map.remove(i);
                        index_adjustment += 1;
                        continue;
                    }

                // Conflicting signatures have identical confidence levels; defer to the previously vetted signature
                } else {
                    debug!("Conflicting signatures at offset {:#X} with the same confidence; first come, first served", this_signature.offset);
                    file_map.remove(i);
                    index_adjustment += 1;
                    continue;
                }

            // Else, if the offsets don't conflict, make sure this signature doesn't fall inside a previously identified signature's data
            } else if this_signature.offset < next_valid_offset {
                debug!(
                    "Signature {} at offset {:#X} contains conflicting data; ignoring",
                    this_signature.name, this_signature.offset
                );
                file_map.remove(i);
                index_adjustment += 1;
                continue;
            }

            // If we've made it this far, make sure this signature's data doesn't extend beyond EOF and that the file data doesn't wrap around
            if this_signature.size > remaining_available_size
                || ((this_signature.offset + this_signature.size) as isize) < 0
            {
                debug!(
                    "Signature {} at offset {:#X} claims its size extends beyond EOF; ignoring",
                    this_signature.name, this_signature.offset
                );
                file_map.remove(i);
                index_adjustment += 1;
                continue;
            }

            // This signature looks OK, update the next_valid_offset to be the end of this signature's data, only if we're fairly confident in the signature
            if this_signature.confidence >= signatures::common::CONFIDENCE_MEDIUM {
                next_valid_offset = this_signature.offset + this_signature.size;
            }
        }

        /*
         * Ideally, all signatures would report their size; some file formats do not specify a size, and the only
         * way to determine the size is to extract the file format (compressed data, for example).
         * For signatures with a reported size of 0, update their size to be the start of the next signature, or EOF.
         * This makes the assumption that there are no false positives or false negatives.
         *
         * False negatives (i.e., there is some other file format or data between this signature and the next that
         * was not correctly identified) is less problematic, as this will overestimate the size of this signature,
         * but most extraction utilities don't care about this extra trailing data being included.
         *
         * False positives (i.e., some data inside of this signature is identified as some other file type) can cause
         * this signature's file data to become truncated, which will inevitably result in a failed, or partial, extraction.
         *
         * Thus, signatures must be very good at validating magic matches and eliminating false positives.
         */
        for i in 0..file_map.len() {
            if file_map[i].size == 0 {
                // Index of the next file map entry, if any
                let next_index = i + 1;

                // By default, assume this signature goes to EOF
                let mut next_offset: usize = file_data.len();

                // If there are more entries in the file map
                if next_index < file_map.len() {
                    // Look through all remaining file map entries for one with medium to high confidence
                    for file_map_entry in file_map.iter().skip(next_index) {
                        if file_map_entry.confidence >= signatures::common::CONFIDENCE_MEDIUM {
                            // If a signature of at least medium confidence is found, assume that *this* signature ends there
                            next_offset = file_map_entry.offset;
                            break;
                        }
                    }
                }

                file_map[i].size = next_offset - file_map[i].offset;
                warn!(
                    "Signature {}:{:#X} size is unknown; assuming size of {:#X} bytes",
                    file_map[i].name, file_map[i].offset, file_map[i].size
                );
            } else {
                debug!(
                    "Signature {}:{:#X} has a reported size of {:#X} bytes",
                    file_map[i].name, file_map[i].offset, file_map[i].size
                );
            }
        }

        debug!("Found {} valid signatures", file_map.len());

        file_map
    }

    /// Extract all extractable signatures found in a file.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_binwalk_rs_529_0() -> Result<binwalk::Binwalk, binwalk::BinwalkError> {
    /// use binwalk::Binwalk;
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let target_path = "/usr/share/man/man2/accept.2.gz".to_string();
    /// let extraction_directory = "/tmp/foobar/extractions".to_string();
    ///
    /// let binwalker = Binwalk::configure(Some(target_path),
    ///                                    Some(extraction_directory),
    ///                                    None,
    ///                                    None,
    ///                                    None,
    ///                                    false)?;
    ///
    /// let file_data = std::fs::read(&binwalker.base_target_file).expect("Unable to read file");
    ///
    /// let scan_results = binwalker.scan(&file_data);
    /// let extraction_results = binwalker.extract(&file_data, &binwalker.base_target_file, &scan_results);
    ///
    /// assert_eq!(scan_results.len(), 1);
    /// assert_eq!(extraction_results.len(),  1);
    /// assert_eq!(std::path::Path::new("/tmp/foobar/extractions/accept.2.gz.extracted/0/decompressed.bin").exists(), true);
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(binwalker)
    /// # } _doctest_main_src_binwalk_rs_529_0(); }
    /// ```
    pub fn extract(
        &self,
        file_data: &[u8],
        file_path: &String,
        file_map: &Vec<signatures::common::SignatureResult>,
    ) -> HashMap<String, extractors::common::ExtractionResult> {
        let mut extraction_results: HashMap<String, extractors::common::ExtractionResult> =
            HashMap::new();

        // Spawn extractors for each extractable signature
        for signature in file_map {
            // Signatures may opt to not perform extraction; honor this request
            if signature.extraction_declined {
                continue;
            }

            // Get the extractor for this signature
            let extractor = self.extractor_lookup_table[&signature.name].clone();

            match &extractor {
                None => continue,
                Some(_) => {
                    // Run an extraction for this signature
                    let mut extraction_result =
                        extractors::common::execute(file_data, file_path, signature, &extractor);

                    if !extraction_result.success {
                        debug!(
                            "Extraction failed for {} (ID: {}) {:#X} - {:#X}",
                            signature.name, signature.id, signature.offset, signature.size
                        );

                        // Calculate all available data from the start of this signature to EOF
                        let available_data = file_data.len() - signature.offset;

                        /*
                         * If extraction failed, it could be due to truncated data (signature matching is not perfect ya know!)
                         * In that case, make one more attempt, this time provide the extractor all the data possible.
                         */
                        if signature.size < available_data {
                            // Create a duplicate signature, but set its reported size to the length of all available data
                            let mut new_signature = signature.clone();
                            new_signature.size = available_data;

                            debug!(
                                "Trying extraction for {} (ID: {}) again, this time from {:#X} - {:#X}",
                                new_signature.name,
                                new_signature.id,
                                new_signature.offset,
                                new_signature.size
                            );

                            // Re-run the extraction
                            extraction_result = extractors::common::execute(
                                file_data,
                                file_path,
                                &new_signature,
                                &extractor,
                            );
                        }
                    }

                    // Update the HashMap with the result of this extraction attempt
                    extraction_results.insert(signature.id.clone(), extraction_result);
                }
            }
        }

        extraction_results
    }

    /// Analyze a file and optionally extract the file contents.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_binwalk_rs_624_0() -> Result<binwalk::Binwalk, binwalk::BinwalkError> {
    /// use binwalk::Binwalk;
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let target_path = "/usr/share/man/man2/accept.2.gz".to_string();
    /// let extraction_directory = "/tmp/foobar/extractions".to_string();
    ///
    /// let binwalker = Binwalk::configure(Some(target_path),
    ///                                    Some(extraction_directory),
    ///                                    None,
    ///                                    None,
    ///                                    None,
    ///                                    false)?;
    ///
    /// let analysis_results = binwalker.analyze(&binwalker.base_target_file, true);
    ///
    /// assert_eq!(analysis_results.file_map.len(), 1);
    /// assert_eq!(analysis_results.extractions.len(),  1);
    /// assert_eq!(std::path::Path::new("/tmp/foobar/extractions/accept.2.gz.extracted/0/decompressed.bin").exists(), true);
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(binwalker)
    /// # } _doctest_main_src_binwalk_rs_624_0(); }
    /// ```
    pub fn analyze(&self, target_file: &String, do_extraction: bool) -> AnalysisResults {
        // Return value
        let mut results: AnalysisResults = AnalysisResults {
            file_path: target_file.clone(),
            ..Default::default()
        };

        debug!("Analysis start: {}", target_file);

        // Read file into memory
        if let Ok(file_data) = read_file(target_file) {
            // Scan file data for signatures
            info!("Scanning {}", target_file);
            results.file_map = self.scan(&file_data);

            // Only extract if told to, and if there were some signatures found in this file
            if do_extraction && !results.file_map.is_empty() {
                // Extract everything we can
                debug!(
                    "Submitting {} signature results to extractor",
                    results.file_map.len()
                );
                results.extractions = self.extract(&file_data, target_file, &results.file_map);
            }
        }

        debug!("Analysis end: {}", target_file);

        results
    }
}

/// Initializes the extraction output directory
fn init_extraction_directory(
    target_file: &String,
    extraction_directory: &String,
) -> Result<String, std::io::Error> {
    // Create the output directory, equivalent of mkdir -p
    match fs::create_dir_all(extraction_directory) {
        Ok(_) => {
            debug!("Created base output directory: '{}'", extraction_directory);
        }
        Err(e) => {
            error!(
                "Failed to create base output directory '{}': {}",
                extraction_directory, e
            );
            return Err(e);
        }
    }

    // Create a Path for the target file
    let target_path = path::Path::new(&target_file);

    // Build a symlink path to the target file in the extraction directory
    let symlink_target_path_str = format!(
        "{}{}{}",
        extraction_directory,
        path::MAIN_SEPARATOR,
        target_path.file_name().unwrap().to_str().unwrap()
    );

    // Create a path for the symlink target path
    let symlink_path = path::Path::new(&symlink_target_path_str);

    debug!(
        "Creating symlink from {} -> {}",
        symlink_path.display(),
        target_path.display()
    );

    // Create a symlink from inside the extraction directory to the specified target file
    #[cfg(unix)]
    {
        match unix::fs::symlink(target_path, symlink_path) {
            Ok(_) => Ok(symlink_target_path_str),
            Err(e) => {
                error!(
                    "Failed to create symlink {} -> {}: {}",
                    symlink_path.display(),
                    target_path.display(),
                    e
                );
                Err(e)
            }
        }
    }
    #[cfg(windows)]
    {
        match windows::fs::symlink_file(target_path, symlink_path) {
            Ok(_) => {
                return Ok(symlink_target_path_str);
            }
            Err(e) => {
                error!(
                    "Failed to create symlink {} -> {}: {}",
                    symlink_path.display(),
                    target_path.display(),
                    e
                );
                return Err(e);
            }
        }
    }
}

/// Returns true if the signature should be included for file analysis, else returns false.
fn include_signature(
    signature: &signatures::common::Signature,
    include: &Option<Vec<String>>,
    exclude: &Option<Vec<String>>,
) -> bool {
    if let Some(include_signatures) = include {
        for include_str in include_signatures {
            if signature.name.to_lowercase() == include_str.to_lowercase() {
                return true;
            }
        }

        return false;
    }

    if let Some(exclude_signatures) = exclude {
        for exclude_str in exclude_signatures {
            if signature.name.to_lowercase() == exclude_str.to_lowercase() {
                return false;
            }
        }

        return true;
    }

    true
}

/// Some SignatureResult fields need to be auto-populated.
fn signature_result_auto_populate(
    signature_result: &mut signatures::common::SignatureResult,
    signature: &signatures::common::Signature,
) {
    signature_result.id = Uuid::new_v4().to_string();
    signature_result.name = signature.name.clone();
    signature_result.always_display = signature.always_display;
}
