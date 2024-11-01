mod common;

#[test]
fn pdf_integration() {
    const SIGNATURE_TYPE: &str = "arcadyan";
    const INPUT_FILE_NAME: &str = "arcadyan.bin";
    let _ = common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
