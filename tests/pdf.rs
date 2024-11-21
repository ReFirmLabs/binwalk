mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "pdf";
    const INPUT_FILE_NAME: &str = "pdf.bin";

    let expected_signature_offsets: Vec<usize> = vec![0];
    let expected_extraction_offsets: Vec<usize> = vec![];

    let results = common::run_binwalk(SIGNATURE_TYPE, INPUT_FILE_NAME);
    common::assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}
