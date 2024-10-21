use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::mbr::parse_mbr_image;

/// Defines the internal extractor function for MBR partitions
pub fn mbr_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_mbr_partitions),
        ..Default::default()
    }
}

/// Validate and extract partitions from an MBR
pub fn extract_mbr_partitions(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    // Return value
    let mut result = ExtractionResult {
        ..Default::default()
    };

    let available_data = file_data.len() - offset;

    // Parse the MBR header
    if let Ok(mbr_header) = parse_mbr_image(&file_data[offset..]) {
        // Make sure there is at least one valid partition
        if !mbr_header.partitions.is_empty() {
            // Make sure the reported size of the MBR does not extend beyond EOF
            if available_data >= mbr_header.image_size {
                // Everything looks ok
                result.success = true;
                result.size = Some(mbr_header.image_size);

                // Do extraction if requested
                if output_directory.is_some() {
                    // Chroot extracted files into the output directory
                    let chroot = Chroot::new(output_directory);

                    // Loop through each partition
                    for (partition_count, partition) in mbr_header.partitions.iter().enumerate() {
                        // Partition names are not unique, output file will be: "<name>_partition.<partition count>"
                        let partition_name =
                            format!("{}_partition.{}", partition.name, partition_count);

                        // Carve out the partition
                        result.success = chroot.carve_file(
                            partition_name,
                            file_data,
                            partition.start,
                            partition.size,
                        );

                        // If partition extraction failed, quit and report a failure
                        if !result.success {
                            break;
                        }
                    }
                }
            }
        }
    }

    result
}
