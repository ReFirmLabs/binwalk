mod common;

#[test]
fn pdf_integration() {
    const SIGNATURE_TYPE: &str = "riff";
    const INPUT_FILE_NAME: &str = "riff.bin";
    let _ = common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
