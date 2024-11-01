use binwalk::{AnalysisResults, Binwalk};

pub fn integration_test(signature_filter: &str, file_name: &str) -> AnalysisResults {
    // Build the path to the input file
    let file_path = std::path::Path::new("tests")
        .join("inputs")
        .join(file_name)
        .display()
        .to_string();

    // Build the path to the output directory
    let output_directory = std::path::Path::new(&std::env::temp_dir().display().to_string())
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

    // Each test is expected to have a single result at offset 0 in the file
    assert!(results.file_map.len() == 1);
    assert!(results.file_map[0].offset == 0);
    
    // Tests which support extraction are expected to have a single successful extraction
    if !results.extractions.is_empty() {
        assert!(results.extractions.len() == 1);
        assert!(results.extractions[&results.file_map[0].id].success);
    }

    // Clean up the output directory
    let _ = std::fs::remove_dir_all(output_directory);

    results
}
