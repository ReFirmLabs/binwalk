use crate::common::epoch_to_string;
use crate::extractors::squashfs::squashfs_v4_be_extractor;
use crate::signatures::common::{SignatureError, SignatureResult, CONFIDENCE_HIGH};
use crate::structures::squashfs::{parse_squashfs_header, parse_squashfs_uid_entry};
use std::collections::HashMap;

/// Human readable description
pub const DESCRIPTION: &str = "SquashFS file system";

/// All of the known magic bytes that could indicate the beginning of a SquashFS image
pub fn squashfs_magic() -> Vec<Vec<u8>> {
    vec![
        b"sqsh".to_vec(),
        b"hsqs".to_vec(),
        b"sqlz".to_vec(),
        b"qshs".to_vec(),
        b"tqsh".to_vec(),
        b"hsqt".to_vec(),
        b"shsq".to_vec(),
    ]
}

/// Responsible for parsing and validating a suspected SquashFS image header
pub fn squashfs_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    const SQUASHFSV4: usize = 4;

    let squashfs_compression_types = HashMap::from([
        (0, "unknown"),
        (1, "gzip"),
        (2, "lzma"),
        (3, "lzo"),
        (4, "xz"),
        (5, "lz4"),
        (6, "zstd"),
    ]);

    let mut result = SignatureResult {
        size: 0,
        offset,
        description: DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let available_data: usize = file_data.len() - offset;

    // Parse the squashfs header
    if let Ok(squashfs_header) = parse_squashfs_header(&file_data[offset..]) {
        // Sanity check the reported image size
        if squashfs_header.image_size <= available_data {
            /*
             * To better validate SquashFS images, we want to verify at least some of the SquashFS image contents.
             * There are situations where the SquashFS header itself is valid and in-tact, but the data is not; for example,
             * gzipping a SquashFS image often leaves some of the SquashFS data uncompressed, since SquashFS images are already
             * compressed and the gzip utility realizes that it cannot further compress some sections. This can result in the
             * contents of the gzipped data containing an uncorrupted copy of the SquashFS header, while some of the SquashFS
             * image contents are gzipped compressed.
             *
             * The easiest field to validate seems to be the UID table pointer, which is an offset in the SquashFS image whre
             * the UID table resides. This table is just an array of 64-bit pointers, each one pointing to a compressed data block
             * which contains the actual UIDs. Validate that the UID table pointer is sane, *and* that the first 64-bit pointer
             * in the UID table is sane.
             */

            // Get the offset of the UID table, an array of pointers to metadata blocks containing lists of user IDs
            let uid_table_start: usize = offset + squashfs_header.uid_table_start;

            // Validate that the UID table pointer points to a location after the end of the SquashFS header (it's usually at the end of the image)
            if uid_table_start > squashfs_header.header_size {
                // Get the UID table data
                if let Some(uid_entry_data) = file_data.get(uid_table_start..) {
                    // Parse one entry from the UID table
                    if let Ok(uid_entry) = parse_squashfs_uid_entry(
                        uid_entry_data,
                        squashfs_header.major_version,
                        &squashfs_header.endianness,
                    ) {
                        // Make sure the first UID table entry is either 0, or falls within the bounds of the SquashFS image data
                        if (uid_entry == 0)
                            || (uid_entry > squashfs_header.header_size
                                && uid_entry <= squashfs_header.image_size)
                        {
                            // Format the modified time into something human readable
                            let create_date = epoch_to_string(squashfs_header.timestamp as u32);

                            // Make sure the compression type is supported
                            if squashfs_compression_types.contains_key(&squashfs_header.compression)
                            {
                                let compression_type_str = squashfs_compression_types
                                    [&squashfs_header.compression]
                                    .to_string();

                                // Standard SquashFSv4 is little endian only; devices that implement a custom big endian version must use a custom extractor
                                if squashfs_header.major_version == SQUASHFSV4
                                    && squashfs_header.endianness == "big"
                                {
                                    result.preferred_extractor = Some(squashfs_v4_be_extractor());
                                }

                                result.size = squashfs_header.image_size;
                                result.description = format!("{}, {} endian, version: {}.{}, compression: {}, inode count: {}, block size: {}, image size: {} bytes, created: {}", result.description,
                                                                                                                                                                                   squashfs_header.endianness,
                                                                                                                                                                                   squashfs_header.major_version,
                                                                                                                                                                                   squashfs_header.minor_version,
                                                                                                                                                                                   compression_type_str,
                                                                                                                                                                                   squashfs_header.inode_count,
                                                                                                                                                                                   squashfs_header.block_size,
                                                                                                                                                                                   squashfs_header.image_size,
                                                                                                                                                                                   create_date);

                                return Ok(result);
                            }
                        }
                    }
                }
            }
        }
    }

    Err(SignatureError)
}
