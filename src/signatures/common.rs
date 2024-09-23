use crate::extractors;
use serde::{Serialize, Deserialize};

// Some pre-defined confidence levels for SignatureResult structures
pub const CONFIDENCE_LOW: u8 = 0;
pub const CONFIDENCE_MEDIUM: u8 = 128;
pub const CONFIDENCE_HIGH: u8 = 250;
pub const CONFIDENCE_HIGHER_THAN_SNOOP_DOG: u8 = 255;

#[derive(Debug, Clone)]
pub struct SignatureError;

/*
 * All signature parsers take a vector of u8 bytes, and an offset into that vector where the signature's magic bytes were found.
 * They return either a SignatureResult struct, or, if the signature is not valid, a SignatureError.
 */
pub type SignatureParser = fn (&Vec<u8>, usize) -> Result<SignatureResult, SignatureError>;

/*
 * This struct is returned by all signature parser functions (see: SignatureParser and Signature, below).
 * The id and name fields are automatically populated, and need not be set by parser functions.
 * At the very least, parser functions should define the offset and description fields.
 * Note that if a SignatureResult contains a size of 0, it is assumed to extend to the beginning of the next signature, or EOF, whichever comes first (see: binwalk.rs).
 * Sortable by offset.
 */
#[derive(Debug, Default, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct SignatureResult {
    // File offset where this signature starts
    pub offset: usize,
    // Automatically populated; see: binwalk::signature_result_auto_populate
    pub id: String,
    // Size of the signature data, 0 if unknown
    pub size: usize,
    // Automatically populated; see: binwalk::signature_result_auto_populate
    pub name: String,
    // One of CONFIDENCE_LOW, CONFIDENCE_MEDIUM, CONFIDENCE_HIGH; default is CONFIDENCE_LOW
    pub confidence: u8,
    // Human readable description of this signature
    pub description: String,
    // Automatically populated; see: binwalk::signature_result_auto_populate
    pub always_display: bool,
    // Set to true to disable extraction for this particular signature result (default: false)
    pub extraction_declined: bool,
    // Signatures may specify a preferred extractor, which overrides the default extractor specified in magic.rs
    #[serde(skip_deserializing, skip_serializing)]
    pub preferred_extractor: Option<extractors::common::Extractor>,
}

/*
 * There must be a signature struct defined for each signature (see: signatures::magic::patterns).
 * Signature.magic is an array of "magic" byte patterns that are associated with the signature.
 * Signature.parser is a function of type SignatureParser, responsible for parsing and validating hits on those "magic" byte patterns.
 * If always_display is true, then this signature will always be displayed (during recursive extraction files with no extractable signatures
 * are not displayed by default; see main.rs).
 * 
 */
#[derive(Debug, Clone)]
pub struct Signature {
    // Unique name for the signature (no whitespace)
    pub name: String,
    // Set to true if this is a short signature; it will only be matched at the beginning of a file
    pub short: bool,
    // List of magic byte patterns associated with this signature
    pub magic: Vec<Vec<u8>>,
    // Offset of magic bytes from the beginning of the file; only relevant for short signatures
    pub magic_offset: usize,
    // Human readable description of this signature
    pub description: String,
    // If true, will always display files that contain this signature, even during recursive extraction
    pub always_display: bool,
    // Specifies the signature parser to invoke for magic match validation
    pub parser: SignatureParser,
    // Specifies the extractor to use when extracting this file type
    pub extractor: Option<extractors::common::Extractor>,
}
