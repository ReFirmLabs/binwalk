use crate::extractors;
use serde::{Deserialize, Serialize};

/// Some pre-defined confidence levels for SignatureResult structures
pub const CONFIDENCE_LOW: u8 = 0;
pub const CONFIDENCE_MEDIUM: u8 = 128;
pub const CONFIDENCE_HIGH: u8 = 250;

/// Return value of SignatureParser upon error
#[derive(Debug, Clone)]
pub struct SignatureError;

/// Type definition for signature parser functions
///
/// ## Arguments
///
/// All signature parsers are passed two arguments: a vector of u8 bytes, and an offset into that vector where the signature's magic bytes were found.
///
/// ## Return values
///
/// Each signature parser is responsible for parsing and validating signature candidates.
///
/// They must return either a SignatureResult struct if validation succeeds, or a SignatureError if validation fails.
pub type SignatureParser = fn(&[u8], usize) -> Result<SignatureResult, SignatureError>;

/// Describes a valid identified file signature
///
/// ## Construction
///
/// The SignatureResult struct is returned by all SignatureParser functions upon success.
///
/// The `id`, `name`, and `always_display` fields are automatically populated after being returned by a SignatureParser function, and need not be set by the SignatureParser function.
///
/// At the very least, SignatureParser functions should define the `offset` and `description` fields.
///
/// ## Additional Notes
///
/// If a SignatureResult contains a `size` of `0` (the default value), it is assumed to extend to the beginning of the next signature, or EOF, whichever comes first.
///
/// SignatureResult structs are sortable by `offset`.
///
/// SignatureResult structs can be JSON serialized/deserialized with [serde](https://crates.io/crates/serde).
#[derive(Debug, Default, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct SignatureResult {
    /// File/data offset where this signature starts
    pub offset: usize,
    /// A UUID uniquely identifying this signature result; auto-populated
    pub id: String,
    /// Size of the signature data, 0 if unknown
    pub size: usize,
    /// A unique name for this signature type, auto-populated from the signature definition in Signature.name
    pub name: String,
    /// One of CONFIDENCE_LOW, CONFIDENCE_MEDIUM, CONFIDENCE_HIGH; default is CONFIDENCE_LOW
    pub confidence: u8,
    /// Human readable description of this signature
    pub description: String,
    /// If true, always display this signature result; auto-populated from the signature definition in Signature.always_display
    pub always_display: bool,
    /// Set to true to disable extraction for this particular signature result (default: false)
    pub extraction_declined: bool,
    /// Signatures may specify a preferred extractor, which overrides the default extractor specified in the Signature.extractor definition
    #[serde(skip_deserializing, skip_serializing)]
    pub preferred_extractor: Option<extractors::common::Extractor>,
}

/// Defines a file signature to search for, and how to extract that file type
#[derive(Debug, Clone)]
pub struct Signature {
    /// Unique name for the signature (no whitespace)
    pub name: String,
    /// Set to true if this is a short signature; it will only be matched at the beginning of a file
    pub short: bool,
    /// List of magic byte patterns associated with this signature
    pub magic: Vec<Vec<u8>>,
    /// Offset of magic bytes from the beginning of the file; only relevant for short signatures
    pub magic_offset: usize,
    /// Human readable description of this signature
    pub description: String,
    /// If true, will always display files that contain this signature, even during recursive extraction
    pub always_display: bool,
    /// Specifies the signature parser to invoke for magic match validation
    pub parser: SignatureParser,
    /// Specifies the extractor to use when extracting this file type
    pub extractor: Option<extractors::common::Extractor>,
}
