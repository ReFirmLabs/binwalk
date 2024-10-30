//! # File / Data Signatures
//!
//! Creating a signature to identify a particular file or data type is composed of two parts:
//!
//! 1. Defining the signature's attributes
//! 2. Writing a parser to parse and validate potential signature matches
//!
//! ## Defining a Signature
//!
//! Signatures are defined using the `signatures::common::Signature` struct. This structure stores critical information
//! about a signature, such as the signature name, the magic bytes that are associated with the signature, and which extractor
//! to use (if any) to extract the data associated with the signature.
//!
//! ### Example
//!
//! ```ignore
//! use binwalk::extractors::foobar::foobar_extractor;
//! use binwalk::signatures::common::Signature;
//! use binwalk::signatures::foobar::foobar_parser;
//!
//! // FooBar file signature
//! let foobar_signature = Signature {
//!     // A unique name for the signature, no spaces; signatures can be included/excluded from analysis based on this attribute
//!     name: "foobar".to_string(),
//!     // Set to true for signatures with very short magic bytes; they will only be matched at file offset 0
//!     short: false,
//!     // Offset from the start of the file to the "magic" bytes; only really relevant for short signatures
//!     magic_offset: 0,
//!     // Most signatures will want to set this to false and let the code in main.rs determine if/when to display
//!     always_display: false,
//!     // The magic bytes associated with this signature; there may be more than one set of magic bytes per signature
//!     magic: vec![b"\xF0\x00\xBA\xA2".to_vec()],
//!     // This is the parser function to call to validate magic byte matches
//!     parser: foobar_parser,
//!     // A short human-readable description of the signature
//!     description: "FooBar file".to_string(),
//!     // The extractor to use to extract this file/data type
//!     extractor: Some(foobar_extractor()),
//! };
//! ```
//!
//! Internally, Binwalk keeps a list of `Signature` definitions in `magic.rs`.
//!
//! ## Signature Parsers
//!
//! Signature parsers are at the heart of each defined signature. They parse and validate magic matches to ensure accuracy and
//! determine the total size of the file data (if possible).
//!
//! Signature parsers must conform to the `signatures::common::SignatureParser` type definition.
//! They are provided two arguments: the raw file data, and an offset into the file data where the signature's magic bytes were found.
//!
//! Signature parsers must parse and validate the expected signature data, and return either a `signatures::common::SignatureResult`
//! structure on success, or a `signatures::common::SignatureError` on failure.
//!
//! ### Example
//!
//! ```ignore
//! use binwalk::extractors::foobar::extract_foobar_file;
//! use binwalk::signatures::common::{SignatureResult, SignatureError, CONFIDENCE_HIGH};
//!
//! /// This function is responsible for parsing and validating the FooBar file system data whenever the "magic bytes"
//! /// are found inside a file. It is provided access to the entire file data, and an offset into the file data where
//! /// the magic bytes were found. On success, it will return a signatures::common::SignatureResult structure.
//! ///
//! pub fn foobar_parser(file_data: &Vec<u8>, offset: usize) -> Result<SignatureResult, SignatureError> {
//!    /*
//!     * This will be returned if the format of the suspected FooBar file system looks correct.
//!     * We will update it later with more information, but for now just define what is known
//!     * (the offset where the FooBar file  starts, the human-readable description, and
//!     * a confidence level), and leave the remaining fields at their defaults.
//!     *
//!     * Note that confidence level is chosen somewhat arbitrarily, and should be one of:
//!     *
//!     *   - CONFIDENCE_LOW (the default)
//!     *   - CONFIDENCE_MEDIUM
//!     *   - CONFIDENCE_HIGH
//!     *
//!     * In this case the extractor and header parser (defined elsewhere) validate CRC's, so if those pass,
//!     * the confidence that this is in fact a FooBar file type is high.
//!     */
//!    let mut result = SignatureResult {
//!         offset: offset,
//!         description: "FooBar file".to_string(),
//!         confidence: CONFIDENCE_HIGH,
//!         ..Default::default()
//!    };
//!
//!    /*
//!     * The internal FooBar file extractor already parses the header and validates the data CRC. By passing it an output
//!     * directory of None, it will still parse and validate the data, but without performing an extraction.
//!     */
//!    let dry_run = extact_foobar_file(file_data, offset, None);
//!
//!    // The extractor should have reported success, as well as the total size of the file data
//!    if dry_run.success == true {
//!        if let Some(file_size) = dry_run.size {
//!            // Update the reported size and human-readable description and return the result
//!            result.size = file_size;
//!            result.description = format!("{}, total size: {} bytes", result.description, result.size);
//!            return Ok(result);
//!        }
//!    }
//!
//!    // Something didn't look right about this file data, it is likely a false positive, so return an error
//!    return Err(SignatureError);
//! }
//! ```
pub mod aes;
pub mod androidsparse;
pub mod apfs;
pub mod arcadyan;
pub mod autel;
pub mod binhdr;
pub mod btrfs;
pub mod bzip2;
pub mod cab;
pub mod cfe;
pub mod chk;
pub mod common;
pub mod compressd;
pub mod copyright;
pub mod cpio;
pub mod cramfs;
pub mod deb;
pub mod dlob;
pub mod dmg;
pub mod dtb;
pub mod ecos;
pub mod efigpt;
pub mod elf;
pub mod ext;
pub mod fat;
pub mod gif;
pub mod gpg;
pub mod gzip;
pub mod hashes;
pub mod iso9660;
pub mod jboot;
pub mod jffs2;
pub mod jpeg;
pub mod linux;
pub mod luks;
pub mod lz4;
pub mod lzfse;
pub mod lzma;
pub mod lzop;
pub mod mbr;
pub mod ntfs;
pub mod openssl;
pub mod packimg;
pub mod pcap;
pub mod pchrom;
pub mod pdf;
pub mod pe;
pub mod pem;
pub mod pjl;
pub mod png;
pub mod qnx;
pub mod rar;
pub mod riff;
pub mod romfs;
pub mod rsa;
pub mod rtk;
pub mod seama;
pub mod sevenzip;
pub mod squashfs;
pub mod srec;
pub mod svg;
pub mod tarball;
pub mod tplink;
pub mod trx;
pub mod ubi;
pub mod uefi;
pub mod uimage;
pub mod vxworks;
pub mod wince;
pub mod xz;
pub mod yaffs;
pub mod zip;
pub mod zlib;
pub mod zstd;
