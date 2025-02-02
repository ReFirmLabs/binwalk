use crate::structures::common::{self, StructureError};

#[derive(Debug, Default, Clone)]
pub struct BMPFileHeader {
    pub size: usize,
    pub bitmap_bits_offset: usize,
}

pub fn parse_bmp_file_header(bmp_data: &[u8]) -> Result<BMPFileHeader, StructureError> {
    // https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapfileheader
    let bmp_header_structure = vec![
        ("bfType", "u16"),
        ("bfSize", "u32"),
        ("bfReserved1", "u16"),
        ("bfReserved2", "u16"),
        ("bfOffBits", "u32"),
    ];

    if let Ok(bmp_header) = common::parse(bmp_data, &bmp_header_structure, "little") {
        let bmp_data_size = bmp_data.len();

        // The BMP file size cannot be bigger than bmp_data
        if bmp_data_size < bmp_header["bfSize"] {
            return Err(StructureError);
        }

        // The file size cannot be 0
        if bmp_header["bfSize"] == 0 {
            return Err(StructureError);
        }

        // The offset cannot be 0
        if bmp_header["bfOffBits"] == 0 {
            return Err(StructureError);
        }

        // The offset cannot be bigger than the file
        if bmp_header["bfOffBits"] > bmp_data_size {
            return Err(StructureError);
        }

        // If everything is Ok so far, return a BMPFileHeader
        return Ok(BMPFileHeader {
            size: bmp_header["bfSize"],
            bitmap_bits_offset: bmp_header["bfOffBits"],
        });
    }

    Err(StructureError)
}

// https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapv5header
// "The number of bytes required by the structure. Applications should use this member to determine which bitmap information header structure is being used."
pub fn get_dib_header_size(bmp_data: &[u8]) -> Result<usize, StructureError> {
    let valid_header_sizes = [
        12,  // BITMAPCOREHEADER
        40,  // BITMAPINFOHEADER
        108, // BITMAPV4HEADER
        124,
    ];

    let header_size = u32::from_le_bytes(bmp_data[..4].try_into().unwrap());

    if !valid_header_sizes.contains(&header_size) {
        return Err(StructureError);
    }

    Ok(header_size as usize)
}
