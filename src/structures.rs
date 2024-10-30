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
//! To write a structure parser for a simple, fictional, `FooBar` file header:
//!
//! ```no_run
//! use binwalk::common::{crc32, get_cstring};
//! use binwalk::structures::common::{self, StructureError};
//!
//! #[derive(Debug, Default, Clone)]
//! pub struct FooBarHeader {
//!     pub data_crc: usize,
//!     pub data_size: usize,
//!     pub header_size: usize,
//!     pub original_file_name: String,
//! }
//!
//! /// This function parses and validates the FooBar file header.
//! /// It returns a FooBarHeader struct on success, StructureError on failure.
//! fn parse_foobar_header(foobar_data: &[u8]) -> Result<FooBarHeader, StructureError> {
//!     // The header CRC is calculated over the first 13 bytes of the header (everything except the header_crc field)
//!     const HEADER_CRC_LEN: usize = 13;
//!
//!     // Define a data structure; structure members must be in the order in which they appear in the data
//!     let foobar_struct = vec![
//!         ("magic", "u32"),
//!         ("flags", "u8"),
//!         ("data_size", "u32"),
//!         ("data_crc", "u32"),
//!         ("header_crc", "u32"),
//!         // NULL-terminated original file name immediately follows the header structure
//!     ];
//!
//!     let struct_size: usize = common::size(&foobar_struct);
//!
//!     // Parse the provided data in accordance with the layout defined in foobar_struct, interpret fields as little endian
//!     if let Ok(foobar_header) = common::parse(foobar_data, &foobar_struct, "little") {
//!         
//!         if let Some(crc_data) = foobar_data.get(0..HEADER_CRC_LEN) {
//!             // Validate the header CRC
//!             if foobar_header["header_crc"] == (crc32(crc_data) as usize) {
//!                 // Get the NULL-terminated file name that immediately follows the header structure
//!                 if let Some(file_name_bytes) = foobar_data.get(struct_size..) {
//!                     let file_name = get_cstring(file_name_bytes);
//!
//!                     // The file name should be non-zero in length
//!                     if file_name.len() > 0 {
//!                         return Ok(FooBarHeader{
//!                             data_crc: foobar_header["data_crc"],
//!                             data_size: foobar_header["data_size"],
//!                             header_size: struct_size + file_name.len() + 1,  // Total header size is structure size + name length + NULL byte
//!                             original_file_name: file_name.clone(),
//!                         });
//!                     }
//!                 }
//!             }
//!         }
//!     }
//!
//!     return Err(StructureError);
//! }
//! ```

pub mod androidsparse;
pub mod apfs;
pub mod autel;
pub mod binhdr;
pub mod btrfs;
pub mod cab;
pub mod chk;
pub mod common;
pub mod cpio;
pub mod cramfs;
pub mod deb;
pub mod dlob;
pub mod dmg;
pub mod dtb;
pub mod efigpt;
pub mod elf;
pub mod ext;
pub mod fat;
pub mod gif;
pub mod gzip;
pub mod iso9660;
pub mod jboot;
pub mod jffs2;
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
pub mod pe;
pub mod png;
pub mod qnx;
pub mod rar;
pub mod riff;
pub mod romfs;
pub mod rtk;
pub mod seama;
pub mod sevenzip;
pub mod squashfs;
pub mod svg;
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
pub mod zstd;
