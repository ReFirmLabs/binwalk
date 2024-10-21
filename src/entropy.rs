use crate::common::read_file;
use entropy::shannon_entropy;
use log::error;
use plotters::prelude::*;
use serde::{Deserialize, Serialize};
use std::path;

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
fn blocks(data: &[u8]) -> Vec<BlockEntropy> {
    const MIN_BLOCK_SIZE: usize = 1024;
    const NUM_DATA_POINTS: usize = 4096 * 10;

    let mut offset: usize = 0;
    let mut entropy_blocks: Vec<BlockEntropy> = vec![];
    let mut block_size: usize = (data.len() as f64 / NUM_DATA_POINTS as f64).ceil() as usize;

    if block_size < MIN_BLOCK_SIZE {
        block_size = MIN_BLOCK_SIZE;
    }

    while offset < data.len() {
        let mut block = BlockEntropy {
            ..Default::default()
        };

        block.start = offset;
        block.end = block.start + block_size;

        if block.end > data.len() {
            block.end = data.len();
        }

        block.entropy = shannon_entropy(&data[block.start..block.end]);

        entropy_blocks.push(block);

        offset += block_size;
    }

    entropy_blocks
}

/// Generate a plot of a file's entropy.
/// Will output a file to the current working directory with the name `<file_name>.png`.
pub fn plot(file_path: impl Into<String>) -> Result<FileEntropy, EntropyError> {
    const FILE_EXTENSION: &str = "png";
    const SHANNON_MAX_VALUE: i32 = 8;
    const IMAGE_PIXEL_WIDTH: u32 = 2048;
    const IMAGE_PIXEL_HEIGHT: u32 = ((IMAGE_PIXEL_WIDTH as f64) * 0.6) as u32;

    let target_file: String = file_path.into();

    // Get the base name of the target file
    let target_file_name = path::Path::new(&target_file)
        .file_name()
        .unwrap()
        .to_str()
        .unwrap();

    let mut file_entropy = FileEntropy {
        file: format!("{}.{}", target_file_name, FILE_EXTENSION),
        ..Default::default()
    };

    let png_path = file_entropy.file.clone();

    // Make sure the output file doesn't already exist
    if path::Path::new(&png_path).exists() {
        error!("Cannot create entropy graph {}: File exists", png_path);
        return Err(EntropyError);
    }

    // Read in the target file data
    if let Ok(file_data) = read_file(&target_file) {
        let mut points: Vec<(i32, i32)> = vec![];

        // Calculate the entropy for each file block
        file_entropy.blocks = blocks(&file_data);

        // Convert x, y coordinates into i32's
        for block in &file_entropy.blocks {
            let x = block.start as i32;
            let y = block.entropy.round() as i32;
            points.push((x, y));
        }

        // Use the BitMapBackend to create a PNG, make the background black
        let root_area = BitMapBackend::new(&png_path, (IMAGE_PIXEL_WIDTH, IMAGE_PIXEL_HEIGHT))
            .into_drawing_area();
        root_area.fill(&BLACK).unwrap();

        // Build a 2D chart to plot the file entropy
        let mut ctx = ChartBuilder::on(&root_area)
            .margin(50)
            .set_label_area_size(LabelAreaPosition::Left, 40)
            .set_label_area_size(LabelAreaPosition::Bottom, 40)
            .caption(
                target_file_name,
                TextStyle::from(("sans-serif", 30).into_font()).color(&GREEN),
            )
            .build_cartesian_2d(0..file_data.len() as i32, 0..SHANNON_MAX_VALUE)
            .unwrap();

        // Set the axis colors
        ctx.configure_mesh()
            .axis_style(GREEN)
            .x_label_style(&GREEN)
            .draw()
            .unwrap();

        // Line plot of the entropy points
        ctx.draw_series(LineSeries::new(
            points, //.into_iter().map(|(x, y)| (x, y)),
            &YELLOW,
        ))
        .unwrap();
    }

    /*
     * Plotter code doesn't throw any errors if graph file creation fails.
     * Make sure the output file was created.
     */
    if !path::Path::new(&png_path).exists() {
        error!(
            "Failed to create entropy graph {}: possible permissions error?",
            png_path
        );
        return Err(EntropyError);
    }

    Ok(file_entropy)
}
