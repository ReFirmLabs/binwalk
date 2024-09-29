use log::error;
use serde::{Deserialize, Serialize};
use serde_json;
use std::fs;
use std::io;
use std::io::Seek;
use std::io::Write;

use crate::entropy::FileEntropy;
use crate::binwalk::AnalysisResults;

#[derive(Debug, Serialize, Deserialize)]
pub enum JSONType {
    Entropy(FileEntropy),
    Analysis(AnalysisResults),
}

/*
 * If file does not exist, write [\n<data>,\n]
 * Else, seek to EOF -1 , write ",\n<data>,\n]"
 */
pub fn log(json_file: &Option<String>, results: JSONType) {
    const JSON_LIST_START: &str = "[\n";
    const JSON_LIST_END: &str = "\n]";
    const JSON_COMMA_SEPERATOR: &str = ",\n";

    match json_file {
        None => return,
        Some(file_name) => {
            // Convert analysis results to JSON
            match serde_json::to_string_pretty(&results) {
                Err(e) => panic!("Failed to convert analysis results to JSON: {}", e),
                Ok(json) => {
                    // Open file for reading and writing, create if does not already exist
                    match fs::OpenOptions::new()
                        .create(true)
                        .read(true)
                        .write(true)
                        .open(&file_name)
                    {
                        Err(e) => {
                            error!("Failed to open JSON log file '{}': {}", file_name, e);
                            return;
                        }
                        Ok(mut fp) => {
                            // Seek to the end of the file and get the cursor position
                            match fp.seek(io::SeekFrom::End(0)) {
                                Err(e) => {
                                    error!("Failed to see to end of JSON file: {}", e);
                                    return;
                                }
                                Ok(pos) => {
                                    if pos == 0 {
                                        // If EOF is at offset 0, this file is empty and needs an opening JSON list character
                                        write_to_json_file(&fp, JSON_LIST_START.to_string());
                                    } else {
                                        // If there is already data in the file we want to overwrite the last byte, which should be a closing JSON list character, with a comma
                                        if let Err(e) = fp.seek(io::SeekFrom::Start(
                                            pos - (JSON_LIST_END.len() as u64),
                                        )) {
                                            error!("Failed to seek to EOF-1 in JSON file: {}", e);
                                            return;
                                        } else {
                                            write_to_json_file(
                                                &fp,
                                                JSON_COMMA_SEPERATOR.to_string(),
                                            );
                                        }
                                    }

                                    // Write the JSON data to file
                                    write_to_json_file(&fp, json);

                                    // Write a closing JSON list character to file
                                    write_to_json_file(&fp, JSON_LIST_END.to_string());
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

fn write_to_json_file(mut fp: &fs::File, data: String) {
    match fp.write_all(data.as_bytes()) {
        Ok(_) => return,
        Err(e) => error!("Failed to write to JSON log file: {}", e),
    }
}
