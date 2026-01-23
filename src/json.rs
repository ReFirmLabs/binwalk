use log::error;
use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::io::Seek;
use std::io::Write;

use crate::binwalk::AnalysisResults;
use crate::display;
#[cfg(feature = "entropy-plot")]
use crate::entropy::FileEntropy;

const STDOUT: &str = "-";
const JSON_LIST_START: &str = "[\n";
const JSON_LIST_END: &str = "\n]\n";
const JSON_LIST_SEP: &str = ",\n";

#[derive(Debug, Serialize, Deserialize)]
pub enum JSONType {
    #[cfg(feature = "entropy-plot")]
    Entropy(FileEntropy),
    Analysis(AnalysisResults),
}

#[derive(Debug, Default, Clone)]
pub struct JsonLogger {
    pub json_file: Option<String>,
    pub json_file_initialized: bool,
}

impl JsonLogger {
    pub fn new(log_file: Option<String>) -> JsonLogger {
        let mut new_instance = JsonLogger {
            ..Default::default()
        };

        if log_file.is_some() {
            new_instance.json_file = Some(log_file.unwrap().clone());
        }

        new_instance
    }

    pub fn close(&self) {
        self.write_json(JSON_LIST_END);
    }

    pub fn log(&mut self, results: JSONType) {
        // Convert analysis results to JSON
        match serde_json::to_string_pretty(&results) {
            Err(e) => error!("Failed to convert analysis results to JSON: {e}"),
            Ok(json) => {
                if !self.json_file_initialized {
                    self.write_json(JSON_LIST_START);
                    self.json_file_initialized = true;
                } else {
                    self.write_json(JSON_LIST_SEP);
                }
                self.write_json(&json);
            }
        }
    }

    fn write_json(&self, data: &str) {
        if let Some(log_file) = &self.json_file {
            if log_file == STDOUT {
                display::print_plain(false, data);
            } else {
                // Open file for reading and writing, create if does not already exist
                match fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .read(true)
                    .open(log_file)
                {
                    Err(e) => {
                        error!("Failed to open JSON log file '{log_file}': {e}");
                    }
                    Ok(mut fp) => {
                        // Seek to the end of the file and get the cursor position
                        match fp.seek(io::SeekFrom::End(0)) {
                            Err(e) => {
                                error!("Failed to seek to end of JSON file: {e}");
                            }
                            Ok(_) => {
                                if let Err(e) = fp.write_all(data.as_bytes()) {
                                    error!("Failed to write to JSON log file: {e}");
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
