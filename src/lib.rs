//! Rust library for identifying, and optionally extracting, files embedded inside other files.
//!
//! ## Example
//!
//!```no_run
//! use binwalk::Binwalk;
//!
//! fn main() {
//!     // Create a new Binwalk instance
//!     let binwalker = Binwalk::new();
//!
//!     // Read in the data you want to analyze
//!     let file_data = std::fs::read("/tmp/firmware.bin").expect("Failed to read from file");
//!
//!     // Scan the file data and print the results
//!     for result in binwalker.scan(&file_data) {
//!         println!("{:#?}", result);
//!     }
//! }
//! ```
mod binwalk;
pub mod common;
pub mod extractors;
mod magic;
pub mod signatures;
pub mod structures;
pub use binwalk::{AnalysisResults, Binwalk};
