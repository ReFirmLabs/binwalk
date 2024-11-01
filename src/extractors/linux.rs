use crate::extractors;

/// Describes how to run the vmlinux-to-elf utility to convert raw kernel images to ELF files
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::linux::linux_kernel_extractor;
///
/// match linux_kernel_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn linux_kernel_extractor() -> extractors::common::Extractor {
    extractors::common::Extractor {
        do_not_recurse: true,
        utility: extractors::common::ExtractorType::External("vmlinux-to-elf".to_string()),
        extension: "bin".to_string(),
        arguments: vec![
            // Input file
            extractors::common::SOURCE_FILE_PLACEHOLDER.to_string(),
            // Output file
            "linux_kernel.elf".to_string(),
        ],
        exit_codes: vec![0],
    }
}
