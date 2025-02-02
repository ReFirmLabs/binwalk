mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "bmp";
    const INPUT_FILE_NAME: &str = "bmp.bin";

    let expected_signature_offsets: Vec<usize> = vec![0xB7F94, 0x10AFEC];
    let expected_extraction_offsets: Vec<usize> = vec![0xB7F94, 0x10AFEC];

    let results = common::run_binwalk(SIGNATURE_TYPE, INPUT_FILE_NAME);
    common::assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}
