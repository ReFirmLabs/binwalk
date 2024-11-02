mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "riff";
    const INPUT_FILE_NAME: &str = "riff.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
