mod common;

#[test]
fn integration_test_truncated_zip() {
    const SIGNATURE_TYPE: &str = "zip";
    const INPUT_FILE_NAME: &str = "zip_truncated.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
