mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "cramfs";
    const INPUT_FILE_NAME: &str = "cramfs.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
