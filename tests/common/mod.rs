use binwalk::{AnalysisResults, Binwalk};

/// Convenience function for running an integration test against the specified file, with the provided signature filter.
/// Assumes that there will be one signature result and one extraction result at file offset 0.
#[allow(dead_code)]
pub fn integration_test(signature_filter: &str, file_name: &str) {
    let expected_signature_offsets: Vec<usize> = vec![0];
    let expected_extraction_offsets: Vec<usize> = vec![0];

    // Run binwalk, get analysis/extraction results
    let results = run_binwalk(signature_filter, file_name);

    // Assert that there was a valid signature and successful result at, and only at, file offset 0
    assert_results_ok(
        results,
        expected_signature_offsets,
        expected_extraction_offsets,
    );
}

/// Assert that there was a valid signature match and corresponding extraction at, and only at, the specified file offsets
pub fn assert_results_ok(
    results: AnalysisResults,
    signature_offsets: Vec<usize>,
    extraction_offsets: Vec<usize>,
) {
    // Assert that the number of signature results and extractions match the expected results
    assert!(results.file_map.len() == signature_offsets.len());
    assert!(results.extractions.len() == extraction_offsets.len());

    // Assert that each signature match was at an expected offset and that extraction, if expected, was successful
    for signature_result in results.file_map {
        assert!(signature_offsets.contains(&signature_result.offset));
        if extraction_offsets.contains(&signature_result.offset) {
            assert!(results.extractions[&signature_result.id].success);
        }
    }
}

/// Run Binwalk, with extraction, against the specified file, with the provided signature filter
pub fn run_binwalk(signature_filter: &str, file_name: &str) -> AnalysisResults {
    // Build the path to the input file
    let file_path = std::path::Path::new("tests")
        .join("inputs")
        .join(file_name)
        .display()
        .to_string();

    // Build the path to the output directory
    let output_directory = std::path::Path::new("tests")
        .join("binwalk_integration_test_extractions")
        .display()
        .to_string();

    // Delete the output directory, if it exists
    let _ = std::fs::remove_dir_all(&output_directory);

    // Configure binwalk
    let binwalker = Binwalk::configure(
        Some(file_path),
        Some(output_directory.clone()),
        Some(vec![signature_filter.to_string()]),
        None,
        None,
        false,
    )
    .expect("Binwalk initialization failed");

    // Run analysis
    let results = binwalker.analyze(&binwalker.base_target_file, true);

    // Clean up the output directory
    let _ = std::fs::remove_dir_all(output_directory);

    results
}
