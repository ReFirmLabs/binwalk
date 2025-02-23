use crate::structures::common;
use crate::structures::common::StructureError;
use std::collections::HashMap;

#[derive(Debug, Default, Clone)]
pub struct QcowHeader {
    pub version: u8,
    pub storage_media_size: u64,
    pub cluster_block_bits: u8,
    pub encryption_method: String,
}

pub fn parse_qcow_header(qcow_data: &[u8]) -> Result<QcowHeader, StructureError> {
    let qcow_basehdr_structure = vec![("magic", "u32"), ("version", "u32")];
    let qcow_header_v1_structure = vec![
        ("backing_filename_offset", "u64"),
        ("backing_filename_size", "u32"),
        ("modification_timestamp", "u32"),
        ("storage_media_size", "u64"),
        ("cluster_block_bits", "u8"),
        ("level2_table_bits", "u8"),
        ("reserved1", "u16"),
        ("encryption_method", "u32"),
        ("level1_table_offset", "u64"),
    ];
    let qcow_header_v2_structure = vec![
        ("backing_filename_offset", "u64"),
        ("backing_filename_size", "u32"),
        ("cluster_block_bits", "u32"),
        ("storage_media_size", "u64"),
        ("encryption_method", "u32"),
        ("level1_table_refs", "u32"),
        ("level1_table_offset", "u64"),
        ("refcount_table_offset", "u64"),
        ("refcount_table_clusters", "u32"),
        ("snapshot_count", "u32"),
        ("snapshot_offset", "u64"),
    ];
    let qcow_header_v3_structure = vec![
        ("backing_filename_offset", "u64"),
        ("backing_filename_size", "u32"),
        ("cluster_block_bits", "u32"),
        ("storage_media_size", "u64"),
        ("encryption_method", "u32"),
        ("level1_table_refs", "u32"),
        ("level1_table_offset", "u64"),
        ("refcount_table_offset", "u64"),
        ("refcount_table_clusters", "u32"),
        ("snapshot_count", "u32"),
        ("snapshot_offset", "u64"),
        ("incompatible_feature_flags", "u64"),
        ("compatible_feature_flags", "u64"),
        ("autoclear_feature_flags", "u64"),
        ("refcount_order", "u32"),
        ("file_hdr_size", "u32"), // 104 or 112
    ];

    let encryption_methods = HashMap::from([(0, "None"), (1, "AES128-CBC"), (2, "LUKS")]);

    if let Ok(qcow_base_header) = common::parse(qcow_data, &qcow_basehdr_structure, "big") {
        let qcow_version = qcow_base_header["version"];
        let qcow_data = qcow_data.get(8..).ok_or(StructureError)?;
        let qcow_header = match qcow_version {
            1 => common::parse(qcow_data, &qcow_header_v1_structure, "big"),
            2 => common::parse(qcow_data, &qcow_header_v2_structure, "big"),
            3 => common::parse(qcow_data, &qcow_header_v3_structure, "big"),
            _ => Err(StructureError),
        }?;

        let encryption_method = encryption_methods
            .get(&qcow_header["encryption_method"])
            .ok_or(StructureError)?
            .to_string();

        let cluster_block_bits = *qcow_header
            .get("cluster_block_bits")
            .filter(|&&bits| (9..=21).contains(&bits))
            .ok_or(StructureError)?;

        // sanity check: existing offsets need to be aligned to cluster boundary
        if let Some(offset) = qcow_header.get("level1_table_offset") {
            if offset % (1 << cluster_block_bits) != 0 {
                return Err(StructureError);
            }
        }
        if let Some(offset) = qcow_header.get("refcount_table_offset") {
            if offset % (1 << cluster_block_bits) != 0 {
                return Err(StructureError);
            }
        }
        if let Some(offset) = qcow_header.get("snapshot_offset") {
            if offset % (1 << cluster_block_bits) != 0 {
                return Err(StructureError);
            }
        }

        return Ok(QcowHeader {
            version: qcow_version as u8,
            storage_media_size: qcow_header["storage_media_size"] as u64,
            cluster_block_bits: cluster_block_bits as u8,
            encryption_method,
        });
    }

    Err(StructureError)
}
