/// Credit to:
/// https://arxiv.org/html/2407.05064v1
/// https://github.com/RedaOps/minifs-extractor

use crate::extractors;
use crate::extractors::common::{Chroot, ExtractionResult, Extractor};
use crate::structures::minifs;
use liblzma::stream::{Action, Stream};
use std::u64;

pub struct DecompressedFile {
    pub path: String,
    pub filename: String,
    pub data: Vec<u8>,
}

pub fn extract(content: &[u8]) -> (Vec<DecompressedFile>, usize) {

    let r = minifs::parse_minifs_file(content);
    if r.is_err() {
        return (vec![], 0);
    }

    let mf = r.unwrap();

    const MEM_LIMIT: u64 = 4 * 1024 * 1024 * 1024;

    let decompressed_chunks = mf.chunks.iter()
        .map(|x| {
            let Ok(mut decompressor) = Stream::new_auto_decoder(MEM_LIMIT, 0) else { panic!() };

            let compressed_chunk = minifs::get_offset(
                &content,
                mf.offsets.raw_chunks_offset + x.chunk_offset as usize,
                x.chunk_size.try_into().unwrap(),
            );

            let mut decompressed_chunk: Vec<u8> = Vec::with_capacity(x.decompressed_size as usize);
            match decompressor.process_vec(
                &compressed_chunk,
                &mut decompressed_chunk,
                Action::Run,
            ) {
                Err(_) => {
                    panic!();
                }
                Ok(_status) => {}
            }

            if decompressed_chunk.len() != x.decompressed_size as usize {
                panic!("LZMA decompressed chunk doesn't match size");
            }

            decompressed_chunk
        })
        .collect::<Vec<Vec<u8>>>();
    println!("[+] Decompressed {} chunks", decompressed_chunks.len());

    (mf.files
        .iter()
        .map(|x| {
            let path = minifs::read_string(
                &content,
                mf.offsets.ton_offset + x.ton_path_offset as usize,
            );
            let filename = minifs::read_string(
                &content,
                mf.offsets.ton_offset + x.ton_file_name_offset as usize,
            );

            let data = minifs::get_offset(
                &decompressed_chunks[x.chunk_number as usize],
                x.offset_in_chunk as usize,
                x.file_size as usize,
            );

            DecompressedFile {
                path,
                filename,
                data,
            }
        })
        .collect::<Vec<DecompressedFile>>(), mf.file_size)
}


pub fn minifs_extractor() -> Extractor {
    Extractor {
        utility: extractors::common::ExtractorType::Internal(extract_minifs),
        ..Default::default()
    }
}

pub fn extract_minifs(
    file_data: &[u8],
    offset: usize,
    output_directory: Option<&str>,
) -> ExtractionResult {
    // If no name is provided in the minifs header, use this as the output file name

    let mut result = ExtractionResult {
        ..Default::default()
    };

    let Some(data) = file_data.get(offset..) else { panic!("Gaaaa!") };
    let (files, size) = extract(&*Vec::from(data));

    if  output_directory.is_some() {
        let chroot = Chroot::new(output_directory);

        for file in files {
            let _x = chroot.create_directory(file.path.clone());
            chroot.create_file(
                format!("{}/{}", file.path, file.filename),
                &*file.data);
        }
    }

    result.success = true;
    result.size = Option::from(size);

    result
}
