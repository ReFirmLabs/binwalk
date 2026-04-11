mod common;

#[test]
fn integration_test_single_kernel_eva() {
    const SIGNATURE_TYPE: &str = "eva";
    const INPUT_FILE_NAME: &str = "eva_single_kernel.bin";
    common::integration_test(SIGNATURE_TYPE, INPUT_FILE_NAME);
}
