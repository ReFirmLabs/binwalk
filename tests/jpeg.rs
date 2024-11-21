mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "jpeg";
    const INPUT_FILE_NAME: &str = "jpeg.bin";

    let expected_signature_offsets: Vec<usize> = vec![0, 0x15BBE];
    let expected_extraction_offsets: Vec<usize> = vec![0, 0x15BBE];

    let results = common::run_binwalk(SIGNATURE_TYPE, INPUT_FILE_NAME);
    common::assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}
