use log::{debug, info};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::binwalk;
use crate::common::read_file;
use crate::extractors;
use crate::signatures;

/*
 * Contains all information about an analysis, including identified signatures and extraction status.
 */
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct AnalysisResults {
    pub file_path: String,
    pub file_map: Vec<signatures::common::SignatureResult>,
    pub extractions: HashMap<String, extractors::common::ExtractionResult>,
}

pub fn analyze(
    binworker: &binwalk::Binwalk,
    target_file: &String,
    do_extraction: bool,
) -> AnalysisResults {
    // Return value
    let mut results: AnalysisResults = AnalysisResults {
        file_path: target_file.clone(),
        ..Default::default()
    };

    // Read file into memory
    if let Ok(file_data) = read_file(target_file) {
        // Scan file data for signatures
        info!("Scanning {}", target_file);
        results.file_map = binworker.scan(&file_data);

        // Only extract if told to, and if there were some signatures found in this file
        if do_extraction == true && results.file_map.len() > 0 {
            // Extract everything we can
            debug!(
                "Submitting {} signature results to extractor",
                results.file_map.len()
            );
            results.extractions =
                binworker.extract(&file_data, &target_file, &results.file_map);
        }
    }

    return results;
}
