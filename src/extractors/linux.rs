use crate::extractors;

/// Describes how to run the vmlinux-to-elf utility to convert raw kernel images to ELF files
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
