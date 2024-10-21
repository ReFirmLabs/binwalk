use crate::common::crc32;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor, ExtractorType};
use crate::structures::trx::parse_trx_header;

/// Defines the internal TRX extractor
pub fn trx_extractor() -> Extractor {
    Extractor {
        utility: ExtractorType::Internal(extract_trx_partitions),
        ..Default::default()
    }
}

/// Internal extractor for TRX partitions
pub fn extract_trx_partitions(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&String>,
) -> ExtractionResult {
    const CRC_DATA_START_OFFSET: usize = 12;

    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Get the TRX data and parse the header
    if let Some(trx_header_data) = file_data.get(offset..) {
        if let Ok(trx_header) = parse_trx_header(trx_header_data) {
            let crc_data_start = offset + CRC_DATA_START_OFFSET;
            let crc_data_end = crc_data_start + trx_header.total_size - CRC_DATA_START_OFFSET;

            if let Some(crc_data) = file_data.get(crc_data_start..crc_data_end) {
                if trx_crc32(crc_data) == trx_header.checksum {
                    result.success = true;
                    result.size = Some(trx_header.total_size);

                    // If extraction was requested, carve the TRX partitions
                    if output_directory.is_some() {
                        let chroot = Chroot::new(output_directory);

                        for i in 0..trx_header.partitions.len() {
                            let next_partition: usize = i + 1;
                            let this_partition_relative_offset: usize = trx_header.partitions[i];
                            let this_partition_absolute_offset: usize =
                                offset + this_partition_relative_offset;
                            let mut this_partition_size: usize =
                                trx_header.total_size - this_partition_relative_offset;

                            if next_partition < trx_header.partitions.len() {
                                this_partition_size = trx_header.partitions[next_partition]
                                    - this_partition_relative_offset;
                            }

                            let this_partition_file_name = format!("partition_{}.bin", i);
                            result.success = chroot.carve_file(
                                &this_partition_file_name,
                                file_data,
                                this_partition_absolute_offset,
                                this_partition_size,
                            );

                            if !result.success {
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    result
}

fn trx_crc32(crc_data: &[u8]) -> usize {
    (crc32(crc_data) ^ 0xFFFFFFFF) as usize
}
