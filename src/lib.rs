//! Rust library for identifying, and optionally extracting, files embedded inside other files.
mod binwalk;
pub mod common;
pub mod extractors;
mod magic;
pub mod signatures;
pub mod structures;
pub use binwalk::{AnalysisResults, Binwalk};
