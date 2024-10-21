use crate::binwalk::AnalysisResults;
use crate::extractors;
use crate::signatures;
use colored::ColoredString;
use colored::Colorize;
use std::collections::HashMap;
use std::io;
use std::io::Write;
use std::time;

const DELIM_CHARACTER: &str = "-";
const DEFAULT_TERMINAL_WIDTH: u16 = 200;

const COLUMN1_WIDTH: usize = 35;
const COLUMN2_WIDTH: usize = 35;

fn terminal_width() -> usize {
    let terminal_width: u16 = match termsize::get() {
        Some(ts) => ts.cols,
        None => DEFAULT_TERMINAL_WIDTH,
    };

    terminal_width as usize
}

fn line_delimiter() -> String {
    let mut delim: String = "".to_string();

    for _i in 0..terminal_width() {
        delim += DELIM_CHARACTER;
    }

    delim
}

fn center_text(text: &String) -> String {
    let mut padding_width: i32;
    let mut centered_string: String = "".to_string();

    match ((terminal_width() / 2) - (text.len() / 2)).try_into() {
        Err(_e) => padding_width = 0,
        Ok(value) => padding_width = value,
    }

    if padding_width < 0 {
        padding_width = 0;
    }

    for _i in 0..padding_width {
        centered_string += " ";
    }

    centered_string += text;

    centered_string
}

fn pad_to_length(text: &str, len: usize) -> String {
    let mut pad_size: i32;
    let mut padded_string = String::from(text);

    match (len - text.len()).try_into() {
        Err(_e) => pad_size = 0,
        Ok(value) => pad_size = value,
    }

    if pad_size < 0 {
        pad_size = 0;
    }

    for _i in 0..pad_size {
        padded_string += " ";
    }

    padded_string
}

fn line_wrap(text: &str, prefix_size: usize) -> String {
    let mut this_line = "".to_string();
    let mut formatted_string = "".to_string();
    let max_line_size: usize = terminal_width() - prefix_size;

    for word in text.split_whitespace() {
        if (this_line.len() + word.len()) < max_line_size {
            this_line = this_line + word + " ";
        } else {
            formatted_string = formatted_string + &this_line + "\n";
            for _i in 0..prefix_size {
                formatted_string += " ";
            }
            this_line = word.to_string() + " ";
        }
    }

    formatted_string = formatted_string + &this_line;

    return formatted_string.trim().to_string();
}

fn print_column_headers(col1: &str, col2: &str, col3: &str) {
    let header_string = format!(
        "{}{}{}",
        pad_to_length(col1, COLUMN1_WIDTH),
        pad_to_length(col2, COLUMN2_WIDTH),
        col3
    );

    println!("{}", header_string.bold().bright_blue());
}

fn print_delimiter() {
    println!("{}", line_delimiter().bold().bright_blue());
}

fn print_header(title_text: &String) {
    println!();
    println!("{}", center_text(title_text).bold().magenta());
    print_delimiter();
    print_column_headers("DECIMAL", "HEXADECIMAL", "DESCRIPTION");
    print_delimiter();
}

fn print_footer() {
    print_delimiter();
    println!();
}

fn print_signature(signature: &signatures::common::SignatureResult) {
    let decimal_string = format!("{}", signature.offset);
    let hexadecimal_string = format!("{:#X}", signature.offset);
    let display_string = format!(
        "{}{}{}",
        pad_to_length(&decimal_string, COLUMN1_WIDTH),
        pad_to_length(&hexadecimal_string, COLUMN2_WIDTH),
        line_wrap(&signature.description, COLUMN1_WIDTH + COLUMN2_WIDTH)
    );

    if signature.confidence >= signatures::common::CONFIDENCE_HIGH {
        println!("{}", display_string.green());
    } else if signature.confidence >= signatures::common::CONFIDENCE_MEDIUM {
        println!("{}", display_string.yellow());
    } else {
        println!("{}", display_string.red());
    }
}

fn print_signatures(signatures: &Vec<signatures::common::SignatureResult>) {
    for signature in signatures {
        print_signature(signature);
    }
}

fn print_extraction(
    signature: &signatures::common::SignatureResult,
    extraction: Option<&extractors::common::ExtractionResult>,
) {
    let extraction_message: ColoredString;

    match extraction {
        None => {
            extraction_message = format!(
                "[#] Extraction of {} data at offset {:#X} declined",
                signature.name, signature.offset
            )
            .bold()
            .yellow();
        }
        Some(extraction_result) => {
            if extraction_result.success {
                extraction_message = format!(
                    "[+] Extraction of {} data at offset {:#X} completed successfully",
                    signature.name, signature.offset
                )
                .bold()
                .green();
            } else {
                extraction_message = format!(
                    "[-] Extraction of {} data at offset {:#X} failed!",
                    signature.name, signature.offset
                )
                .bold()
                .red();
            }
        }
    }

    println!("{extraction_message}");
}

fn print_extractions(
    signatures: &Vec<signatures::common::SignatureResult>,
    extraction_results: &HashMap<String, extractors::common::ExtractionResult>,
) {
    let mut delimiter_printed: bool = false;

    for signature in signatures {
        let mut printable_extraction: bool = false;
        let mut extraction_result: Option<&extractors::common::ExtractionResult> = None;

        // Only print extraction results if an extraction was attempted or explicitly declined
        if signature.extraction_declined {
            printable_extraction = true
        } else if extraction_results.contains_key(&signature.id) {
            printable_extraction = true;
            extraction_result = Some(&extraction_results[&signature.id]);
        }

        if printable_extraction {
            // Only print the delimiter line once
            if !delimiter_printed {
                print_delimiter();
                delimiter_printed = true;
            }
            print_extraction(signature, extraction_result);
        }
    }
}

pub fn print_analysis_results(quiet: bool, extraction_attempted: bool, results: &AnalysisResults) {
    if quiet {
        return;
    }

    // Print signature results
    print_header(&results.file_path);
    print_signatures(&results.file_map);

    // If extraction was attempted, print extraction results
    if extraction_attempted {
        print_extractions(&results.file_map, &results.extractions);
    }

    // Print the footer text
    print_footer();
}

// Used by print_signature_list
#[derive(Debug, Default, Clone)]
struct SignatureInfo {
    name: String,
    is_short: bool,
    has_extractor: bool,
    extractor: String,
    description: String,
}

pub fn print_signature_list(quiet: bool, signatures: &Vec<signatures::common::Signature>) {
    let mut extractor_count: usize = 0;
    let mut signature_count: usize = 0;
    let mut sorted_descriptions: Vec<String> = vec![];
    let mut signature_lookup: HashMap<String, SignatureInfo> = HashMap::new();

    if quiet {
        return;
    }

    // Print column headers
    print_delimiter();
    print_column_headers(
        "Signature Description",
        "Signature Name",
        "Extraction Utility",
    );
    print_delimiter();

    // Loop through all signatures
    for signature in signatures {
        // Convenience struct for storing some basic info about each signature
        let mut signature_info = SignatureInfo {
            ..Default::default()
        };

        // Keep track of signature name, description, and if the signature is a "short" signature
        signature_info.name = signature.name.clone();
        signature_info.is_short = signature.short;
        signature_info.description = signature.description.clone();

        // Keep track of which signatures have associated extractors, and if so, what type of extractor
        match &signature.extractor {
            None => {
                signature_info.has_extractor = false;
                signature_info.extractor = "None".to_string();
            }
            Some(extractor) => {
                signature_info.has_extractor = true;

                match &extractor.utility {
                    extractors::common::ExtractorType::External(command) => {
                        signature_info.extractor = command.to_string();
                    }
                    extractors::common::ExtractorType::Internal(_) => {
                        signature_info.extractor = "Built-in".to_string();
                    }
                    extractors::common::ExtractorType::None => panic!(
                        "An invalid extractor type exists for the '{}' signature",
                        signature.description
                    ),
                }
            }
        }

        // Increment signature count
        signature_count += 1;

        // If there is an extractor for this signature, increment extractor count
        if signature_info.has_extractor {
            extractor_count += 1;
        }

        // Keep signature descriptions in a separate list, which wil be sorted alphabetically for display
        sorted_descriptions.push(signature_info.description.clone());

        // Lookup table associating signature descriptions with their SignatureInfo struct
        signature_lookup.insert(signature.description.clone(), signature_info.clone());
    }

    // Sort signature descriptions alphabetically
    sorted_descriptions.sort_by_key(|description| description.to_lowercase());

    // Print signatures, sorted alphabetically by description
    for description in sorted_descriptions {
        let siginfo = &signature_lookup[&description];

        let display_line = format!(
            "{}{}{}",
            pad_to_length(&description, COLUMN1_WIDTH),
            pad_to_length(&siginfo.name, COLUMN2_WIDTH),
            siginfo.extractor
        );

        if siginfo.is_short {
            println!("{}", display_line.yellow());
        } else {
            println!("{}", display_line.green());
        }
    }

    print_delimiter();
    println!();
    println!("Total signatures: {}", signature_count);
    println!("Extractable signatures: {}", extractor_count);
}

pub fn print_stats(
    quiet: bool,
    run_time: time::Instant,
    file_count: usize,
    signature_count: usize,
    pattern_count: usize,
) {
    const MS_IN_A_SECOND: f64 = 1000.0;
    const SECONDS_IN_A_MINUTE: f64 = 60.0;
    const MINUTES_IN_AN_HOUR: f64 = 60.0;

    let mut file_plural = "";
    let mut units = "milliseconds";
    let mut display_time: f64 = run_time.elapsed().as_millis() as f64;

    if quiet {
        return;
    }

    // Format the output time in a more human-readable manner
    if display_time >= MS_IN_A_SECOND {
        display_time /= MS_IN_A_SECOND;
        units = "seconds";

        if display_time >= SECONDS_IN_A_MINUTE {
            display_time /= SECONDS_IN_A_MINUTE;
            units = "minutes";

            if display_time >= MINUTES_IN_AN_HOUR {
                display_time /= MINUTES_IN_AN_HOUR;
                units = "hours";
            }
        }
    }

    if file_count != 1 {
        file_plural = "s";
    }

    println!(
        "Analyzed {} file{} for {} file signatures ({} magic patterns) in {:.1} {}",
        file_count, file_plural, signature_count, pattern_count, display_time, units
    );
}

pub fn print_plain(quiet: bool, msg: &str) {
    if !quiet {
        print!("{}", msg);
        let _ = io::stdout().flush();
    }
}

pub fn println_plain(quiet: bool, msg: &str) {
    if !quiet {
        println!("{}", msg);
    }
}
