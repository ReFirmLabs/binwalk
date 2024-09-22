use crate::signatures;
use crate::extractors::romfs::extract_romfs;
use crate::structures::romfs::parse_romfs_header;

pub const DESCRIPTION: &str = "RomFS filesystem";

pub fn romfs_magic() -> Vec<Vec<u8>> {
    return vec![b"-rom1fs-".to_vec()];
}

pub fn romfs_parser(file_data: &Vec<u8>, offset: usize) -> Result<signatures::common::SignatureResult, signatures::common::SignatureError> {

    let mut result = signatures::common::SignatureResult {
                                            description: DESCRIPTION.to_string(),
                                            offset: offset,
                                            size: 0,
                                            confidence: signatures::common::CONFIDENCE_HIGH,
                                            ..Default::default()
    };

    // Do an extraction dry run
    let dry_run = extract_romfs(file_data, offset, None);

    // If the dry run was a success, everything should be good to go
    if dry_run.success == true {

        // Parse the RomFS header to get the volume name
        if let Ok(romfs_header) = parse_romfs_header(&file_data[offset..]) {

            // Report the result
            result.size = dry_run.size.unwrap();
            result.description = format!("{}, volume name: \"{}\", total size: {} bytes", result.description, romfs_header.volume_name, result.size);
            return Ok(result);
        }
    }

    return Err(signatures::common::SignatureError);
}
