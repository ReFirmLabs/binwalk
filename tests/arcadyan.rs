mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "arcadyan";
    const INPUT_FILE_NAME: &str = "arcadyan.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
