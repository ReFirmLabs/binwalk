/// Credit to:
/// https://arxiv.org/html/2407.05064v1
/// https://github.com/RedaOps/minifs-extractor

use crate::structures::common::{StructureError};
use std::u64;


/// Describes the internal extractor for carving minifs files to disk
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::minifs::minifs_extractor;
///
/// match minifs_extractor().utility {
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


pub struct MinifsFile {
    pub hdr: MinifsHeader,
    pub offsets: MiniFsOffsets,
    pub files: Vec<ToFEntry>,
    pub chunks: Vec<ToCEntry>,
    pub file_size: usize,
}

#[derive(Debug, Default, Clone)]
pub struct MinifsHeader {
    pub name: u64,
    pub unk1: u64,
    pub ver: u32,
    pub num_files: u32,
    pub unk2: u32,
    pub name_table_size: u32,
}

pub const MINIFS_HEADER_SIZE: usize = 32;

impl MinifsHeader {
    pub fn parse(header: &&[u8]) -> Self {
        Self {
            name: u64::from_be_bytes(header[0..8].try_into().unwrap()),
            unk1: u64::from_be_bytes(header[8..16].try_into().unwrap()),
            ver: u32::from_be_bytes(header[16..20].try_into().unwrap()),
            num_files: u32::from_be_bytes(header[20..24].try_into().unwrap()),
            unk2: u32::from_be_bytes(header[24..28].try_into().unwrap()),
            name_table_size: u32::from_be_bytes(header[28..32].try_into().unwrap()),
        }
    }
}

pub struct MiniFsOffsets {
    /// Table of Names
    pub ton_offset: usize,
    /// Table of Files
    pub tof_offset: usize,
    /// Table of chunks
    pub toc_offset: usize,
    /// Raw chunks
    pub raw_chunks_offset: usize,
}

#[repr(packed)]
pub struct ToFEntry {
    pub ton_path_offset: u32,
    pub ton_file_name_offset: u32,
    pub chunk_number: u32,
    pub offset_in_chunk: u32,
    pub file_size: u32,
}

pub const TOF_ENTRY_SIZE: usize = size_of::<ToFEntry>();

impl ToFEntry {
    pub fn parse(data: [u8; TOF_ENTRY_SIZE]) -> Self {
        Self {
            ton_path_offset: u32::from_be_bytes(data[0..4].try_into().unwrap()),
            ton_file_name_offset: u32::from_be_bytes(data[4..8].try_into().unwrap()),
            chunk_number: u32::from_be_bytes(data[8..12].try_into().unwrap()),
            offset_in_chunk: u32::from_be_bytes(data[12..16].try_into().unwrap()),
            file_size: u32::from_be_bytes(data[16..20].try_into().unwrap()),
        }
    }
}

#[repr(packed)]
pub struct ToCEntry {
    pub chunk_offset: u32,
    pub chunk_size: u32,
    pub decompressed_size: u32,
}

pub const TOC_ENTRY_SIZE: usize = size_of::<ToCEntry>();

impl ToCEntry {
    pub fn parse(data: [u8; TOC_ENTRY_SIZE]) -> Self {
        Self {
            chunk_offset: u32::from_be_bytes(data[0..4].try_into().unwrap()),
            chunk_size: u32::from_be_bytes(data[4..8].try_into().unwrap()),
            decompressed_size: u32::from_be_bytes(data[8..12].try_into().unwrap()),
        }
    }
}

pub fn parse_minifs_file(data: &[u8]) -> Result<MinifsFile, StructureError> {

    let hdr = MinifsHeader::parse(&data);

    let ton_offset = MINIFS_HEADER_SIZE;
    let tof_offset = ton_offset + hdr.name_table_size as usize;
    let toc_offset = tof_offset + (hdr.num_files as usize * TOF_ENTRY_SIZE);

    let mut offsets = MiniFsOffsets {
        ton_offset,
        tof_offset,
        toc_offset,
        // Unknown at this time
        raw_chunks_offset: 0,
    };

    let files : Vec<ToFEntry> = parse_files_internal(&data, &offsets, hdr.num_files);

    let chunks_no = files.last().unwrap().chunk_number + 1;
    offsets.raw_chunks_offset = offsets.toc_offset + (TOC_ENTRY_SIZE * chunks_no as usize);

    let chunks = parse_chunks_internal(&data, &offsets, chunks_no);

    let last_chunk = chunks.last().unwrap();
    let minifs_oef_offset = offsets.raw_chunks_offset + last_chunk.chunk_offset as usize + last_chunk.chunk_size as usize;

    let minifs_file = MinifsFile {
        hdr, offsets, files, chunks,
        file_size: minifs_oef_offset,
    };

    Ok(minifs_file)
}

fn parse_files_internal(
    content: &[u8],
    offsets: &MiniFsOffsets,
    files_no: u32,
) -> Vec<ToFEntry> {
    (0..files_no as usize)
        .map(|i| {
            let entry_offset = offsets.tof_offset + (i * TOF_ENTRY_SIZE);
            ToFEntry::parse(
                content
                    .iter()
                    .copied()
                    .skip(entry_offset)
                    .take(TOF_ENTRY_SIZE)
                    .collect::<Vec<u8>>()
                    .try_into()
                    .unwrap(),
            )
        })
        .collect()
}

fn parse_chunks_internal(
    content: &[u8],
    offsets: &MiniFsOffsets,
    chunks_no: u32,
) -> Vec<ToCEntry> {
    (0..chunks_no as usize)
        .map(|offset| {
            ToCEntry::parse(
                content
                    .iter()
                    .copied()
                    .skip(offsets.toc_offset + offset * TOC_ENTRY_SIZE)
                    .take(TOC_ENTRY_SIZE)
                    .collect::<Vec<u8>>()
                    .try_into()
                    .unwrap(),
            )
        })
        .collect()
}

pub fn get_offset(content: &[u8], offset: usize, len: usize) -> Vec<u8> {
    content.iter().skip(offset).take(len).copied().collect()
}

pub fn read_string(content: &[u8], offset: usize) -> String {
    let mut data = String::new();

    for byte in content.iter().skip(offset) {
        if *byte == 0_u8 {
            return data;
        }

        data.push(*byte as char);
    }

    data
}