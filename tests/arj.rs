use crate::common::assert_results_ok;

mod common;

#[test]
fn integration_test_valid_arj() {
    const SIGNATURE_TYPE: &str = "arj";
    const INPUT_FILE_NAME: &str = "arj.bin";

    let expected_signature_offsets: Vec<usize> = vec![0xD, 0x46];
    let expected_extraction_offsets: Vec<usize> = vec![0xD];

    let results = common::run_binwalk(SIGNATURE_TYPE, INPUT_FILE_NAME);

    assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    )
}
