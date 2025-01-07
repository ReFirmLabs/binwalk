mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "matter_ota";
    const INPUT_FILE_NAME: &str = "matter_ota.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
