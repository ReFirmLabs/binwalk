use crate::structures::common::{self, StructureError};

#[derive(Debug, Default, Clone)]
pub struct DXBCHeader {
    pub size: usize,
    pub chunk_ids: Vec<[u8; 4]>,
}

// http://timjones.io/blog/archive/2015/09/02/parsing-direct3d-shader-bytecode
pub fn parse_dxbc_header(data: &[u8]) -> Result<DXBCHeader, StructureError> {
    let dxbc_header_structure = vec![
        ("magic", "u32"),
        ("signature_p1", "u64"),
        ("signature_p2", "u64"),
        ("one", "u32"),
        ("total_size", "u32"),
        ("chunk_count", "u32"),
    ];

    // Parse the header
    if let Ok(header) = common::parse(data, &dxbc_header_structure, "little") {
        if header["one"] != 1 {
            return Err(StructureError);
        }

        // Sanity check: There are at least 14 known chunks, but most likely no more than 32.
        // Prevents the for loop from spiraling into an OOM on the offchance that both the magic and "one" check pass on garbage data
        if header["chunk_count"] > 32 {
            return Err(StructureError);
        }

        let header_end = common::size(&dxbc_header_structure);

        let mut chunk_ids = vec![];
        for i in 0..header["chunk_count"] {
            let offset_data = data
                .get((header_end + i * 4)..(header_end + i * 4) + 4)
                .ok_or(StructureError)?;
            let offset = u32::from_le_bytes(offset_data.try_into().unwrap()) as usize;

            chunk_ids.push(
                data.get(offset..offset + 4)
                    .ok_or(StructureError)?
                    .try_into()
                    .unwrap(),
            );
        }

        return Ok(DXBCHeader {
            size: header["total_size"],
            chunk_ids,
        });
    }

    Err(StructureError)
}
