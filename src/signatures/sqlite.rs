use crate::signatures::common::{
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, SignatureError, SignatureResult,
};
use crate::structures::sqlite::parse_sqlite3_header;

/// Human readable descriptions
pub const V3_DESCRIPTION: &str = "SQLite 3.x database";
pub const V2_DESCRIPTION: &str = "SQLite 2.x database";

/// SQLite 3 databases start with this
pub fn sqlite3_magic() -> Vec<Vec<u8>> {
    vec![b"SQLite format 3\x00".to_vec()]
}

/// SQLite 2 databases start with this text
pub fn sqlite2_magic() -> Vec<Vec<u8>> {
    vec![b"** This file contains an SQLite".to_vec()]
}

/// Validate a SQLite 3 database signature
pub fn sqlite3_parser(file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    let mut result = SignatureResult {
        offset,
        description: V3_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_HIGH,
        ..Default::default()
    };

    let available_data = file_data.len() - offset;

    if let Ok(sqlite_header) = parse_sqlite3_header(&file_data[offset..]) {
        /*
         * The header records how many pages the database has, but that count is only current if
         * the file has not been written by an older library, so it is only trusted when the pages
         * it describes are actually there.
         */
        let database_size = sqlite_header.page_size * sqlite_header.page_count;

        if database_size <= available_data {
            result.size = database_size;
        }

        result.description = format!(
            "{}, page size: {} bytes, page count: {}, total size: {} bytes",
            result.description, sqlite_header.page_size, sqlite_header.page_count, database_size
        );
        return Ok(result);
    }

    Err(SignatureError)
}

/// Validate a SQLite 2 database signature
pub fn sqlite2_parser(_file_data: &[u8], offset: usize) -> Result<SignatureResult, SignatureError> {
    /*
     * A version 2 database begins with a line of text and a binary header that is not documented
     * anywhere reliable, so there is nothing to validate and no size to report.
     */
    Ok(SignatureResult {
        offset,
        description: V2_DESCRIPTION.to_string(),
        confidence: CONFIDENCE_MEDIUM,
        ..Default::default()
    })
}
