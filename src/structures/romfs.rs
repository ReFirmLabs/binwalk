use crate::common::get_cstring;
use crate::structures::common::{self, StructureError};

/// Stores RomFS header info
#[derive(Default, Debug, Clone)]
pub struct RomFSHeader {
    pub image_size: usize,
    pub header_size: usize,
    pub volume_name: String,
}

/// Parse a RomFS header
pub fn parse_romfs_header(romfs_data: &[u8]) -> Result<RomFSHeader, StructureError> {
    // Maximum amount of data that the RomFS CRC is calculated over
    const MAX_HEADER_CRC_DATA_LEN: usize = 512;

    let header_structure = vec![("magic", "u64"), ("image_size", "u32"), ("checksum", "u32")];

    // Get the size of the defined header structure
    let header_size = common::size(&header_structure);

    // Parse the header structure
    if let Ok(header) = common::parse(romfs_data, &header_structure, "big") {
        // Sanity check the reported image size
        if header["image_size"] > header_size {
            // The volume name is a NULL-terminated string that immediately follows the RomFS header
            if let Some(volume_name_bytes) = romfs_data.get(header_size..) {
                let volume_name = get_cstring(volume_name_bytes);

                let mut crc_data_len: usize = MAX_HEADER_CRC_DATA_LEN;

                if header["image_size"] < crc_data_len {
                    crc_data_len = header["image_size"];
                }

                // Validate the header CRC
                if let Some(crc_data) = romfs_data.get(0..crc_data_len) {
                    if romfs_crc_valid(crc_data) {
                        return Ok(RomFSHeader {
                            image_size: header["image_size"],
                            volume_name: volume_name.clone(),
                            // Volume name has a NULL terminator and is padded to a 16 byte boundary alignment
                            header_size: header_size + romfs_align(volume_name.len() + 1),
                        });
                    }
                }
            }
        }
    }

    Err(StructureError)
}

/// Struct to store info on a RomFS file entry
#[derive(Debug, Default, Clone)]
pub struct RomFSFileHeader {
    pub info: usize,
    pub size: usize,
    pub name: String,
    pub checksum: usize,
    /// Offset to the start of the file data, *relative to the beginning of this header*
    pub data_offset: usize,
    pub file_type: usize,
    pub executable: bool,
    pub symlink: bool,
    pub directory: bool,
    pub regular: bool,
    pub block_device: bool,
    pub character_device: bool,
    pub fifo: bool,
    pub socket: bool,
    /// Offset to the next file header, *relative to the beginning of the RomFS image*
    pub next_header_offset: usize,
}

/// Parse a RomFS file entry
pub fn parse_romfs_file_entry(romfs_data: &[u8]) -> Result<RomFSFileHeader, StructureError> {
    // Bit masks
    const FILE_TYPE_MASK: usize = 0b0111;
    const FILE_EXEC_MASK: usize = 0b1000;
    const NEXT_OFFSET_MASK: usize = 0b11111111_11111111_11111111_11110000;

    // We only support extraction of these file types
    const ROMFS_DIRECTORY: usize = 1;
    const ROMFS_REGULAR_FILE: usize = 2;
    const ROMFS_SYMLINK: usize = 3;
    const ROMFS_BLOCK_DEVICE: usize = 4;
    const ROMFS_CHAR_DEVICE: usize = 5;
    const ROMFS_SOCKET: usize = 6;
    const ROMFS_FIFO: usize = 7;

    let file_header_structure = vec![
        ("next_header_offset", "u32"),
        ("info", "u32"),
        ("size", "u32"),
        ("checksum", "u32"),
    ];

    // Size of the defined file header structure
    let file_header_size = common::size(&file_header_structure);

    // Parse the file header
    if let Ok(file_entry_header) = common::parse(romfs_data, &file_header_structure, "big") {
        // Null terminated file name immediately follows the header
        if let Some(file_name_bytes) = romfs_data.get(file_header_size..) {
            let file_name = get_cstring(file_name_bytes);

            // A file should have a name
            if !file_name.is_empty() {
                // Instantiate a new RomFSEntry structure
                let mut file_header = RomFSFileHeader {
                    ..Default::default()
                };

                // Populate basic info
                file_header.size = file_entry_header["size"];
                file_header.info = file_entry_header["info"];
                file_header.checksum = file_entry_header["checksum"];
                file_header.name = file_name.clone();

                // File data begins immediately after the file header, including the NULL-terminated, 16-byte alignment padded file name
                file_header.data_offset = file_header_size + romfs_align(file_name.len() + 1);

                // These values are encoded into the next header offset field
                file_header.file_type = file_entry_header["next_header_offset"] & FILE_TYPE_MASK;
                file_header.executable =
                    (file_entry_header["next_header_offset"] & FILE_EXEC_MASK) != 0;

                // Set the type of entry that this is
                file_header.fifo = file_header.file_type == ROMFS_FIFO;
                file_header.socket = file_header.file_type == ROMFS_SOCKET;
                file_header.symlink = file_header.file_type == ROMFS_SYMLINK;
                file_header.regular = file_header.file_type == ROMFS_REGULAR_FILE;
                file_header.directory = file_header.file_type == ROMFS_DIRECTORY;
                file_header.block_device = file_header.file_type == ROMFS_BLOCK_DEVICE;
                file_header.character_device = file_header.file_type == ROMFS_CHAR_DEVICE;

                // The next file header offset is an offset from the beginning of the RomFS image
                file_header.next_header_offset =
                    file_entry_header["next_header_offset"] & NEXT_OFFSET_MASK;

                return Ok(file_header);
            }
        }
    }

    Err(StructureError)
}

/// RomFS aligns things to a 16-byte boundary
fn romfs_align(x: usize) -> usize {
    const ALIGNMENT: usize = 16;

    let mut padding: usize = 0;
    let remainder = x % ALIGNMENT;

    if remainder > 0 {
        padding = ALIGNMENT - remainder;
    }

    x + padding
}

/// Pretty simple checksum used by RomFS
fn romfs_crc_valid(crc_data: &[u8]) -> bool {
    let word_size: usize = std::mem::size_of::<u32>();

    // Checksum size must be 4-byte aligned
    if (crc_data.len() % word_size) == 0 {
        let mut i: usize = 0;
        let mut sum: u32 = 0;

        // Sum each word
        while i < crc_data.len() {
            sum += u32::from_be_bytes(crc_data[i..i + word_size].try_into().unwrap());
            i += word_size;
        }

        /*
         * The header checksum is set such that summing the bytes should result in a sum of 0.
         */
        return sum == 0;
    }

    false
}
