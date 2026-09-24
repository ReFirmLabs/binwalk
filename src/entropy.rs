use crate::common::{parse_hex_u64, read_input};
use entropy::shannon_entropy;
use plotly::layout::{Axis, Layout};
use plotly::{ImageFormat, Plot, Scatter};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct EntropyError;

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct BlockEntropy {
    pub end: usize,
    pub start: usize,
    pub entropy: f32,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct FileEntropy {
    pub file: String,
    pub blocks: Vec<BlockEntropy>,
}

/// Splits the supplied data up into blocks and calculates the entropy of each block.
fn blocks(data: &[u8], block_count: usize, start: Option<String>, end: Option<String>, length: Option<String>) -> Vec<BlockEntropy> {
    const BLOCK_COUNT_MAX: usize = 1;

    let block_count = block_count.max(BLOCK_COUNT_MAX);

    let mut offset: usize = 0;

    let start_off: usize = start
        .as_deref()
        .and_then(parse_hex_u64)
        .map(|v| v as usize)
        .unwrap_or(0);

    let end_off: usize = if let Some(len_str) = length.as_deref() {
        parse_hex_u64(len_str)
            .map(|len| start_off.saturating_add(len as usize))
            .unwrap_or(data.len())
            .min(data.len())
    } else if let Some(end_str) = end.as_deref() {
        parse_hex_u64(end_str)
            .map(|v| v as usize)
            .unwrap_or(data.len())
            .min(data.len())
    } else {
        data.len()
    };

    let data_slice: &[u8] = if start_off <= end_off {
        data.get(start_off..end_off).unwrap_or(data)
    } else {
        data
    };

    // block_size usize enforces alignment so block_count can be a non-base2 multiple
    let mut block_size = if data_slice.len() < block_count {
        data_slice.len()
    } else {
        data_slice.len() / block_count
    };

    block_size = block_size.max(1);

    let mut chunker = data_slice.chunks(block_size);
    let mut entropy_blocks: Vec<BlockEntropy> = vec![];

    loop {
        match chunker.next() {
            None => break,
            Some(block_data) => {
                let mut block = BlockEntropy {
                    ..Default::default()
                };

                block.start = offset;
                block.entropy = shannon_entropy(block_data);
                block.end = block.start + block_data.len();

                offset = block.end;
                entropy_blocks.push(block);
            }
        }
    }

    entropy_blocks
}

pub fn plot(
    file_path: impl Into<String>,
    stdin: bool,
    block_count: usize,
    start: Option<String>,
    end: Option<String>,
    length: Option<String>,
    out_file: Option<String>,
) -> Result<FileEntropy, EntropyError> {
    let mut x: Vec<usize> = Vec::new();
    let mut y: Vec<f32> = Vec::new();
    let target_file: String = file_path.into();
    let mut file_entropy = FileEntropy {
        file: target_file.clone(),
        ..Default::default()
    };

    // Read in the target file data
    if let Ok(file_data) = read_input(&target_file, stdin) {
        // Calculate the entropy of each file block
        file_entropy.blocks = blocks(&file_data, block_count, start, end, length);

        for block in &file_entropy.blocks {
            x.push(block.start);
            x.push(block.end);
            y.push(block.entropy);
            y.push(block.entropy);
        }

        let mut plot = Plot::new();
        let trace = Scatter::new(x, y);
        let layout = Layout::new()
            .title("Entropy Graph")
            .x_axis(Axis::new().title("File Offset"))
            .y_axis(Axis::new().title("Entropy").range(vec![0, 8]));

        plot.add_trace(trace);
        plot.set_layout(layout);

        match out_file {
            None => plot.show(),
            Some(out_file_name) => {
                // TODO: Switch to plotly_static, which is the recommended way to do this
                #[allow(deprecated)]
                plot.write_image(&out_file_name, ImageFormat::PNG, 2048, 1024, 1.0);
            }
        }

        return Ok(file_entropy);
    }

    Err(EntropyError)
}
