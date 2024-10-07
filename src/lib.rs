//! Rust library for identifying, and optionally extracting, files embedded inside other files.
mod binwalk;
mod magic;
pub mod common;
pub mod extractors;
pub mod signatures;
pub mod structures;
pub use binwalk::{AnalysisResults, Binwalk};
