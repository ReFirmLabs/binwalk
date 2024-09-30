//! Rust library for identifying, and optionally extracting, files embedded inside other files.
mod binwalk;
mod common;
mod extractors;
mod magic;
mod signatures;

pub mod structures;
pub use common::{crc32, is_offset_safe, read_file, get_cstring, epoch_to_string};
pub use binwalk::{AnalysisResults, Binwalk};
pub use extractors::common::{SOURCE_FILE_PLACEHOLDER, Chroot, ExtractionError, ExtractionResult, Extractor, ExtractorType};
pub use signatures::common::{Signature, SignatureError, SignatureParser, SignatureResult};
