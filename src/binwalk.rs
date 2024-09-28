use aho_corasick::AhoCorasick;
use log::{debug, error, info, warn};
use std::collections::HashMap;
use std::fs;
use std::os::unix;
use std::path;
use uuid::Uuid;

use crate::extractors;
use crate::magic;
use crate::signatures;

#[derive(Debug, Default, Clone)]
pub struct BinwalkError;

#[derive(Debug, Default, Clone)]
pub struct Binwalk {
    // Count of all signatures (short and regular)
    pub signature_count: usize,
    // The base file requested for analysis
    pub base_target_file: String,
    // The base output directory for extracted files
    pub base_output_directory: String,
    // A list of signatures that must start at offset 0
    pub short_signatures: Vec<signatures::common::Signature>,
    // A list of magic bytes to search for throughout the entire file
    pub patterns: Vec<Vec<u8>>,
    // Maps patterns to their corresponding signature
    pub pattern_signature_table: HashMap<usize, signatures::common::Signature>,
    // Maps signatures to their corresponding extractors
    pub extractor_lookup_table: HashMap<String, Option<extractors::common::Extractor>>,
}

impl Binwalk {

    /// Create a new Binwalk instance with all default values.
    /// Equivalent to `Binwalk::new(None, None, None, None, None)`
    pub fn default() -> Binwalk {
        return Binwalk::new(None, None, None, None, None).unwrap();
    }

    /// Create a new Binwalk instance.
    pub fn new(
        target_file_name: Option<String>,
        output_directory: Option<String>,
        include: Option<Vec<String>>,
        exclude: Option<Vec<String>>,
        signatures: Option<Vec<signatures::common::Signature>>
    ) -> Result<Binwalk, BinwalkError> {

        let mut new_instance = Binwalk { ..Default::default() };

        // Target file is optional, especially if being called via the library
        if let Some(target_file) = target_file_name {
            // Set the target file path, make it an absolute path
            new_instance.base_target_file = path::absolute(path::Path::new(&target_file))
                .unwrap()
                .to_str()
                .unwrap()
                .to_string();

            // If an output extraction directory was also specified, initialize it
            if let Some(extraction_directory) = output_directory {
                new_instance.base_output_directory = path::absolute(path::Path::new(&extraction_directory))
                    .unwrap()
                    .to_str()
                    .unwrap()
                    .to_string();

                match init_extraction_directory(&new_instance.base_target_file, &new_instance.base_output_directory)
                {
                    Err(_) => {
                        return Err(BinwalkError);
                    },
                    Ok(new_target_file_path) => {
                        // This is the new base target path (a symlink inside the extraction directory)
                        new_instance.base_target_file = new_target_file_path.clone();
                    },
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
            if include_signature(&signature, &include, &exclude) == false {
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
                if signature.short == true {
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

        return Ok(new_instance);
    }


    /// Scan a file for magic signatures.
    /// Returns a list of validated magic signatures, representing the known contents of the file.
    pub fn scan(&self, file_data: &Vec<u8>) -> Vec<signatures::common::SignatureResult> {
        const FILE_START_OFFSET: usize = 0;

        let mut index_adjustment: usize = 0;
        let mut next_valid_offset: usize = 0;

        // A list of identified signatures, representing a "map" of the file data
        let mut file_map: Vec<signatures::common::SignatureResult> = vec![];

        /*
         * Check beginning of file for shot signatures.
         * These signatures are only valid if they occur at the very beginning of a file.
         * This is typically because the signatures are very short and they are unlikely
         * to occur randomly throughout the file, so this prevents having to validate many
         * false positve matches throughout the file.
         */
        for signature in &self.short_signatures {
            for magic in signature.magic.clone() {
                let magic_start = FILE_START_OFFSET + signature.magic_offset;
                let magic_end = magic_start + magic.len();

                if file_data.len() > magic_end {
                    if file_data[magic_start..magic_end] == magic {
                        debug!(
                            "Found {} short magic match at offset {:#X}",
                            signature.description, magic_start
                        );

                        if let Ok(mut signature_result) = (signature.parser)(&file_data, magic_start) {
                            // Auto populate some signature result fields
                            signature_result_auto_populate(&mut signature_result, &signature);

                            // Add this signature to the file map
                            file_map.push(signature_result.clone());
                            info!(
                                "Found valid {} short signature at offset {:#X}",
                                signature_result.name, FILE_START_OFFSET
                            );

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
        }

        /*
         * Same pattern matching algorithm used by fgrep.
         * This will search for all magic byte patterns in the file data, all at once.
         * https://en.wikipedia.org/wiki/Aho–Corasick_algorithm
         */
        let grep = AhoCorasick::new(self.patterns.clone()).unwrap();

        debug!("Running Aho-Corasick scan");

        // Find all matching patterns in the target file
        for magic_match in grep.find_overlapping_iter(&file_data) {
            // Get the location of the magic bytes inside the file data
            let magic_offset: usize = magic_match.start();

            // No sense processing signatures that we know we don't want
            if magic_offset < next_valid_offset {
                continue;
            }

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
            if let Ok(mut signature_result) = (signature.parser)(&file_data, magic_offset) {
                // Auto populate some signature result fields
                signature_result_auto_populate(&mut signature_result, &signature);

                // Add this signature to the file map
                file_map.push(signature_result.clone());
                next_valid_offset = signature_result.offset + signature_result.size;

                info!(
                    "Found valid {} signature at offset {:#X}",
                    signature_result.name, signature_result.offset
                );

                // If we've found a signature that extends to EOF, no need to keep processing additional signatures
                if next_valid_offset == file_data.len() {
                    break;
                }
            } else {
                debug!(
                    "{} magic match at offset {:#X} is invalid",
                    signature.description, magic_offset
                );
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
            if file_map.len() == 0 || i >= file_map.len() {
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

            // This signature looks OK, update the next_valid_offset to be the end of this signature's data
            next_valid_offset = this_signature.offset + this_signature.size;
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
                    for j in next_index..file_map.len() {
                        if file_map[j].confidence >= signatures::common::CONFIDENCE_MEDIUM {
                            // If a signature of at least medium confidence is found, assume that *this* signature ends there
                            next_offset = file_map[j].offset;
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

        return file_map;
    }


    /// Extract all extractable signatures found in a file.
    /// Returns a HashMap of <SignatureResult.id, ExtractionResult>.
    pub fn extract(
        &self,
        file_data: &Vec<u8>,
        file_path: &String,
        file_map: &Vec<signatures::common::SignatureResult>,
    ) -> HashMap<String, extractors::common::ExtractionResult> {
        let mut extraction_results: HashMap<String, extractors::common::ExtractionResult> =
            HashMap::new();

        // Spawn extractors for each extractable signature
        for signature in file_map {
            // Signatures may opt to not perform extraction; honor this request
            if signature.extraction_declined == true {
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

                    if extraction_result.success == false {
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

        return extraction_results;
    }
}

// Initializes the extraction output directory
fn init_extraction_directory(
    target_file: &String,
    extraction_directory: &String,
) -> Result<String, std::io::Error> {
    // Create the output directory, equivalent of mkdir -p
    match fs::create_dir_all(&extraction_directory) {
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
        symlink_path.to_str().unwrap(),
        target_path.to_str().unwrap()
    );

    // Create a symlink from inside the extraction directory to the specified target file
    match unix::fs::symlink(&target_path, &symlink_path) {
        Ok(_) => {
            return Ok(symlink_target_path_str);
        }
        Err(e) => {
            error!(
                "Failed to create symlink {} -> {}: {}",
                symlink_path.to_str().unwrap(),
                target_path.to_str().unwrap(),
                e
            );
            return Err(e);
        }
    }
}

/*
 * Returns true if the signature should be included for file analysis, else returns false.
 */
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

    return true;
}

/*
 * Some SignatureResult fields need to be auto-populated.
 */
fn signature_result_auto_populate(
    signature_result: &mut signatures::common::SignatureResult,
    signature: &signatures::common::Signature,
) {
    signature_result.id = Uuid::new_v4().to_string();
    signature_result.name = signature.name.clone();
    signature_result.always_display = signature.always_display;
}


