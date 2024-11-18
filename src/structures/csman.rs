use crate::structures::common::{self, StructureError};

/// Struct to store CSMAN header info
#[derive(Debug, Default, Clone)]
pub struct CSManHeader {
    pub compressed: bool,
    pub data_size: usize,
    pub endianness: String,
    pub header_size: usize,
}

/// Parses a CSMAN header
pub fn parse_csman_header(csman_data: &[u8]) -> Result<CSManHeader, StructureError> {
    const COMPRESSED_MAGIC: &[u8] = b"\x78";
    const LITTLE_ENDIAN_MAGIC: usize = 0x4353;

    let csman_header_structure = vec![
        ("magic", "u16"),
        ("unknown1", "u16"),
        ("compressed_size", "u32"),
        ("unknown2", "u32"),
        ("decompressed_size", "u32"),
    ];

    let mut result = CSManHeader {
        ..Default::default()
    };

    // Parse the header
    if let Ok(mut csman_header) = common::parse(csman_data, &csman_header_structure, "big") {
        // Detect the endianness
        if csman_header["magic"] == LITTLE_ENDIAN_MAGIC {
            // If this is a little endian header, re-parse the data as little endian
            if let Ok(csman_header_le) =
                common::parse(csman_data, &csman_header_structure, "little")
            {
                csman_header = csman_header_le.clone();
                result.endianness = "little".to_string();
            }
        } else {
            result.endianness = "big".to_string();
        }

        // Should have been able to determine the endianness
        if !result.endianness.is_empty() {
            result.data_size = csman_header["compressed_size"];
            result.header_size = common::size(&csman_header_structure);
            result.compressed =
                csman_header["compressed_size"] != csman_header["decompressed_size"];

            // If compressed, check the expected compressed magic bytes
            if result.compressed {
                if let Some(compressed_magic) =
                    csman_data.get(result.header_size..result.header_size + COMPRESSED_MAGIC.len())
                {
                    if compressed_magic != COMPRESSED_MAGIC {
                        return Err(StructureError);
                    }
                }
            }

            return Ok(result);
        }
    }

    Err(StructureError)
}

/// Stores info about a single CSMan DAT file entry
#[derive(Debug, Default, Clone)]
pub struct CSManEntry {
    pub size: usize,
    pub eof: bool,
    pub key: usize,
    pub value: Vec<u8>,
}

/// Parses a single CSMan DAT file entry
pub fn parse_csman_entry(
    entry_data: &[u8],
    endianness: &str,
) -> Result<CSManEntry, StructureError> {
    const EOF_TAG: usize = 0;

    // The last entry is just a single 4-byte NULL value
    let csman_last_entry_structure = vec![("eof", "u32")];

    // Entries consist of a 4-byte identifier, a 2-byte size, and a value
    let csman_entry_structure = vec![
        ("key", "u32"),
        ("size", "u16"),
        // value of size bytes immediately follows
    ];

    let mut entry = CSManEntry {
        ..Default::default()
    };

    if let Ok(entry_header) = common::parse(entry_data, &csman_entry_structure, endianness) {
        let value_start: usize = common::size(&csman_entry_structure);
        let value_end: usize = value_start + entry_header["size"];

        if let Some(entry_value) = entry_data.get(value_start..value_end) {
            entry.key = entry_header["key"];
            entry.value = entry_value.to_vec();
            entry.size = common::size(&csman_entry_structure) + entry_value.len();
            return Ok(entry);
        }
    } else if let Ok(entry_header) =
        common::parse(entry_data, &csman_last_entry_structure, endianness)
    {
        if entry_header["eof"] == EOF_TAG {
            entry.eof = true;
            entry.size = common::size(&csman_last_entry_structure);
            return Ok(entry);
        }
    }

    Err(StructureError)
}
