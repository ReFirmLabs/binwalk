mod common;

/// The version 3 input is a real database written by sqlite itself, holding one table of fifty
/// rows across two pages. The version 2 input is the line of text that such a database begins
/// with, which is all there is to go on for that version.
#[test]
fn integration_test() {
    let results = common::run_binwalk("sqlite3", "sqlite3.bin");
    assert!(results.file_map.len() == 1);
    assert!(results.file_map[0].offset == 0);
    assert!(results.file_map[0].size == 8192);
    assert!(results.file_map[0].description.contains("page count: 2"));

    let results = common::run_binwalk("sqlite2", "sqlite2.bin");
    assert!(results.file_map.len() == 1);
    assert!(results.file_map[0].offset == 0);
}
