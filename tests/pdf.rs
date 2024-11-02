mod common;

#[test]
fn integration_test() {
    const SIGNATURE_TYPE: &str = "pdf";
    const INPUT_FILE_NAME: &str = "pdf.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
