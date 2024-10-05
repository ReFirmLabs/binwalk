//! # Data Structure Parsing
//!
//! Both signatures and internal extractors may need to parse data structures used by various file formats.
//! Structure parsing code is placed in the `structures` module.
//!
//! ## Helper Functions
//!
//! There are some definitions and helper functions in `structures::common` that are generally helpful for processing data structures.
//!
//! The `structures::common::parse` function provides a way to parse basic data structures by defining the data structure format,
//! the endianness to use, and the data to cast the structure over. It is heavily used by most structure parsers.
//! It supports the following data types:
//!
//! - u8
//! - u16
//! - u24
//! - u32
//! - u64
//!
//! Regardless of the data type specified, all values are returned as `usize` types.
//! If an error occurs (typically due to not enough data available to process the specified data structure), `Err(structures::common::StructureError)` is returned.
//!
//! The `structures::common::size` function is a convenience function that returns the number of bytes required to parse a defined data structure.
//!
//! The `structures::common::StructureError` struct is typically used by structure parsers to return an error.
//!
//! ## Writing a Structure Parser
//!
//! Structure parsers may be defined however they need to be; there are no strict rules here.
//! Generally, however, they should:
//!
//! - Accept some data to parse
//! - Parse the data structure
//! - Validate the structure fields for correctness
//! - Return an error or success status
//!
//! ### Example
//!
//! To write a parser for a fictional, simple, data structure:
//!
//! ```no_run
//! use binwalk::crc32;
//! use binwalk::structures::common::{self, StructureError};
//!
//! /// This function parses the file structure as defined in my_struct.
//! /// It returns the size reported in the data structure on success.
//! /// It returns structures::common::StructureError on failure.
//! fn parse_my_structure(data: &[u8]) -> Result<usize, StructureError> {
//!     // The header CRC is calculated over the first 15 bytes of the header (everything except the header_crc field)
//!     const CRC_CALC_LEN: usize = 15;
//!
//!     // Define a data structure; structure members must be in the order in which they appear in the data
//!     let my_struct = vec![
//!         ("magic", "u32"),
//!         ("flags", "u8"),
//!         ("size", "u64"),
//!         ("volume_id", "u16"),
//!         ("header_crc", "u32"),
//!     ];
//!
//!     // Parse the provided data in accordance with the layout defined in my_struct, interpret fields as little endian
//!     if let Ok(parsed_structure) = common::parse(data, &my_struct, "little") {
//!         
//!         // Validate the header CRC
//!         if let Some(crc_data) = data.get(0..CRC_CALC_LEN) {
//!             if parsed_structure["header_crc"] == (crc32(crc_data) as usize) {
//!                 return Ok(parsed_structure["size"]);
//!             }
//!         }
//!     }
//!
//!     return Err(StructureError);
//! }
//! ```

pub mod androidsparse;
pub mod cab;
pub mod chk;
pub mod common;
pub mod cpio;
pub mod cramfs;
pub mod deb;
pub mod dlob;
pub mod dmg;
pub mod dtb;
pub mod elf;
pub mod ext;
pub mod gzip;
pub mod iso9660;
pub mod jboot;
pub mod jffs2;
pub mod lz4;
pub mod lzfse;
pub mod lzma;
pub mod lzop;
pub mod mbr;
pub mod openssl;
pub mod packimg;
pub mod pcap;
pub mod pchrom;
pub mod pe;
pub mod png;
pub mod qnx;
pub mod rar;
pub mod riff;
pub mod romfs;
pub mod seama;
pub mod sevenzip;
pub mod squashfs;
pub mod tplink;
pub mod trx;
pub mod ubi;
pub mod uefi;
pub mod uimage;
pub mod vxworks;
pub mod xz;
pub mod yaffs;
pub mod zip;
pub mod zstd;
