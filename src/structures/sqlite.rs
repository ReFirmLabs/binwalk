use crate::structures::common::{self, StructureError};

/// Stores info about a SQLite 3 database header
#[derive(Debug, Default, Clone)]
pub struct SQLite3Header {
    pub page_size: usize,
    pub page_count: usize,
}

/// Parse a SQLite 3 database header
pub fn parse_sqlite3_header(sqlite_data: &[u8]) -> Result<SQLite3Header, StructureError> {
    // A page size of one stands for the largest page size, which does not fit the field
    const LARGE_PAGE_SIZE_FLAG: usize = 1;
    const LARGE_PAGE_SIZE: usize = 65536;
    const MIN_PAGE_SIZE: usize = 512;

    // The file format versions are one for rollback journalling and two for write ahead logging
    const MAX_FORMAT_VERSION: usize = 2;

    let sqlite_structure = vec![
        ("magic_p1", "u64"),
        ("magic_p2", "u64"),
        ("page_size", "u16"),
        ("write_version", "u8"),
        ("read_version", "u8"),
        ("reserved_space", "u8"),
        ("max_payload_fraction", "u8"),
        ("min_payload_fraction", "u8"),
        ("leaf_payload_fraction", "u8"),
        ("change_counter", "u32"),
        ("page_count", "u32"),
    ];

    // These three fields have fixed values, which no other format is likely to reproduce
    const MAX_PAYLOAD_FRACTION: usize = 64;
    const MIN_PAYLOAD_FRACTION: usize = 32;
    const LEAF_PAYLOAD_FRACTION: usize = 32;

    if let Ok(sqlite_header) = common::parse(sqlite_data, &sqlite_structure, "big") {
        let page_size = match sqlite_header["page_size"] {
            LARGE_PAGE_SIZE_FLAG => LARGE_PAGE_SIZE,
            page_size => page_size,
        };

        if page_size >= MIN_PAGE_SIZE
            && page_size.is_power_of_two()
            && sqlite_header["write_version"] <= MAX_FORMAT_VERSION
            && sqlite_header["write_version"] > 0
            && sqlite_header["read_version"] <= MAX_FORMAT_VERSION
            && sqlite_header["read_version"] > 0
            && sqlite_header["max_payload_fraction"] == MAX_PAYLOAD_FRACTION
            && sqlite_header["min_payload_fraction"] == MIN_PAYLOAD_FRACTION
            && sqlite_header["leaf_payload_fraction"] == LEAF_PAYLOAD_FRACTION
        {
            return Ok(SQLite3Header {
                page_size,
                page_count: sqlite_header["page_count"],
            });
        }
    }

    Err(StructureError)
}
