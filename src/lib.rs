//! Rust library for identifying, and optionally extracting, files embedded inside other files.
mod binwalk;
mod common;
mod extractors;
mod magic;
mod signatures;

pub mod structures;
pub use binwalk::{AnalysisResults, Binwalk};
pub use common::{crc32, epoch_to_string, get_cstring, is_offset_safe, read_file};
pub use extractors::common::{
    Chroot, ExtractionError, ExtractionResult, Extractor, ExtractorType, SOURCE_FILE_PLACEHOLDER,
};
pub use signatures::common::{Signature, SignatureError, SignatureParser, SignatureResult};
