//! # File Extractors
//!
//! File extractors may be internal (written in Rust, compiled into Binwalk), or external (command line utilties).
//!
//! While the former are generally faster, safer, and portable, the latter requires very little code to implement.
//!
//! Binwalk relies on various internal and external utilities for automated file extraction.
//!
//! ## External Extractors
//!
//! To implement an external extractor, you must use the `extractors::common::Extractor` struct to define:
//!
//! - The name of a command-line utility to run
//! - What arguments to pass to it
//! - What file extension the utility expects
//! - Which exit codes are considered successful (the default is exit code `0`)
//!
//! ### Example
//!
//! We want to define an external extractor for a new, contrived, file type, `FooBar`. A command-line utility,
//! `unfoobar`, exists, and is typically executed as such:
//!
//! ```bash
//! unfoobar -x -f input_file.bin -o data.foobar
//! ```
//!
//! To define this external utility as an extractor:
//!
//! ```no_run
//! use binwalk::extractors::common::{Extractor, ExtractorType, SOURCE_FILE_PLACEHOLDER};
//!
//! /// This function returns an instance of extractors::common::Extractor, which describes how to run the unfoobar utility.
//! pub fn foobar_extractor() -> Extractor {
//!    // Build and return the Extractor struct
//!    return Extractor {
//!        // This indicates that we are defining an external extractor, named 'unfoobar'
//!        utility: ExtractorType::External("unfoobar".to_string()),
//!        // This is the file extension to use when carving the FooBar file system data to disk
//!        extension: "bin".to_string(),
//!        // These are the arguments to pass to the unfoobar utility
//!        arguments: vec![
//!            "-x".to_string(),           // This argument tells unfoobar to extract the FooBar data
//!            "-o".to_string(),           // Specify an output file
//!            "data.foobar".to_string(),  // The output file name
//!            "-f".to_string(),           // Specify an input file
//!            // This is a special string that will be replaced at run-time with the name of the source file
//!            SOURCE_FILE_PLACEHOLDER.to_string()
//!        ],
//!        // The only valid exit code for this utility is 0
//!        exit_codes: vec![0],
//!        // If set to true, the extracted files will not be analyzed
//!        do_not_recurse: false,
//!        ..Default::default()
//!    };
//! }
//! ```
//!
//! ## Internal Extractors
//!
//! Internal extractors are functions that are repsonsible for extracting the data of a particular file type.
//! They must conform to the `extractors::common::InternalExtractor` type definition.
//!
//! Like external extractors, they are defined using the `extractors::common::Extractor` struct.
//!
//! The internal extraction function will be passed:
//!
//! - The entirety of the file data
//! - An offset inside the file data at which to begin processing data
//! - An output directory for extracted files (optional)
//!
//! If the output directory is `None`, the extractor function should perform a "dry run", processing the intended file format
//! as normal, but must not extract any data; this allows signatures to use the extractor function to validate potential signature
//! matches without performing an actual extraction.
//!
//! Internal extractors must return an `extractors::common::ExtractionResult` struct.
//!
//! Internal extractors should use the `extractors::common::Chroot` API to write files to disk.
//! The methods defined in the `Chroot` struct allow the manipulation of files on disk while ensuring that any file paths
//! accessed do not traverse outside the specified output directory.
//!
//! ### Example
//!
//! ```ignore
//! use binwalk::common::crc32;
//! use binwalk::extractors::common::{Chroot, Extractor, ExtractionResult, ExtractorType};
//! use binwalk::structures::foobar::parse_foobar_header;
//!
//! /// This function *defines* an internal extractor; it is not the actual extractor
//! pub fn foobar_extractor() -> Extractor {
//!    // Build and return the Extractor struct
//!     return Extractor {
//!         // This specifies the function extract_foobar_file as the internal extractor to use
//!         utility: ExtractorType::Internal(extract_foobar_file),
//!         ..Default::default()
//!     };
//! }
//!
//! /// This function extracts the contents of a FooBar file
//! pub fn extract_foobar_file(file_data: Vec<u8>, offset: usize, output_directory: Option<&String>) -> ExtractionResult {
//!
//!     // This will be the return value
//!     let mut result = ExtractionResult{..Default::default()};
//!
//!     // Get the FooBar file data, which starts at the specified offset
//!     if let Some(foobar_data) = file_data.get(offset..) {
//!         // Parse and validate the FooBar file header; this function is defined in the structures module
//!         if let Ok(foobar_header) = parse_foobar_header(foobar_data) {
//!             // Data CRC is calculated over data_size bytes, starting at the end of the FooBar header
//!             let crc_start = foobar_header.header_size;
//!             let crc_end = crc_start + foobar_header.data_size;
//!
//!             if let Some(crc_data) = foobar_data.get(crc_start..crc_end){
//!                 // Validate the data CRC
//!                 if foobar_header.data_crc == (crc32(crc_data) as usize) {
//!                     // Report the total size of the FooBar file, including header and data
//!                     result.size = Some(foobar_header.header_size + foobar_header.data_size);
//!
//!                     // If an output directory was specified, extract the contents of the FooBar file to disk
//!                     if !output_directory.is_none() {
//!                         // Chroot file I/O inside the specified output directory
//!                         let chroot = Chroot::new(output_directory);
//!
//!                         // The FooBar file format is very simple: just a header, followed by the data we want to extract.
//!                         // Carve the FooBar data to disk, and set result.success to true if this succeeds.
//!                         result.success = chroot.carve_file(foobar_header.original_file_name,
//!                                                            foobar_data,
//!                                                            foobar_header.header_size,
//!                                                            foobar_header.data_size);
//!                     } else {
//!                         // Nothing else to do, consider this a success
//!                         result.success = true;
//!                     }
//!                 }
//!             }
//!         }
//!     }
//!
//!     return result;
//! }
//! ```

pub mod androidsparse;
pub mod apfs;
pub mod arcadyan;
pub mod autel;
pub mod bzip2;
pub mod cab;
pub mod common;
pub mod dmg;
pub mod dtb;
pub mod dumpifs;
pub mod gif;
pub mod gzip;
pub mod inflate;
pub mod jboot;
pub mod jffs2;
pub mod jpeg;
pub mod linux;
pub mod lz4;
pub mod lzfse;
pub mod lzma;
pub mod lzop;
pub mod mbr;
pub mod pcap;
pub mod pem;
pub mod png;
pub mod rar;
pub mod riff;
pub mod romfs;
pub mod sevenzip;
pub mod squashfs;
pub mod srec;
pub mod svg;
pub mod tarball;
pub mod trx;
pub mod tsk;
pub mod ubi;
pub mod uefi;
pub mod uimage;
pub mod vxworks;
pub mod wince;
pub mod yaffs2;
pub mod zlib;
pub mod zstd;
