use log::{info, debug };
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

use crate::binwalk;
use crate::extractors;
use crate::signatures;
use crate::common::read_file;

/*
 * Contains all information about an analysis, including identified signatures and extraction status.
 */
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct AnalysisResults {
    pub file_path: String,
    pub file_map: Vec<signatures::common::SignatureResult>,
    pub extractions: HashMap<String, extractors::common::ExtractionResult>,
}

pub fn analyze(bwconfig: &binwalk::BinwalkConfig, target_file: &String, do_extraction: bool) -> AnalysisResults {
    // Return value
    let mut results: AnalysisResults = AnalysisResults { file_path: target_file.clone(), ..Default::default() };

    // Read file into memory
    if let Ok(file_data) = read_file(target_file) {
        // Scan file data for signatures
        info!("Scanning {}", target_file);
        results.file_map = binwalk::scan(&bwconfig, &file_data);

        // Only extract if told to, and if there were some signatures found in this file
        if do_extraction == true && results.file_map.len() > 0 {
            // Extract everything we can
            debug!("Submitting {} results for extraction", results.file_map.len());
            results.extractions = binwalk::extract(&bwconfig, &file_data, &target_file, &results.file_map);
        }
    }

    return results;
}
