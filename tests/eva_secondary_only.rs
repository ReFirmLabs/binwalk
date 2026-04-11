mod common;

#[test]
fn integration_test_secondary_only_eva() {
    const SIGNATURE_TYPE: &str = "eva";
    const INPUT_FILE_NAME: &str = "eva_secondary_only.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
