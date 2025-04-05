use binwalk::AnalysisResults;
use log::{debug, error, info};
use std::collections::VecDeque;
use std::panic;
use std::process;
use std::sync::mpsc;
use std::thread;
use std::time;
use threadpool::ThreadPool;

mod binwalk;
mod cliparser;
mod common;
mod display;
mod entropy;
mod extractors;
mod json;
mod magic;
mod signatures;
mod structures;

fn main() {
    // File name used when reading from stdin
    const STDIN: &str = "stdin";

    // Only use one thread if unable to auto-detect available core info
    const DEFAULT_WORKER_COUNT: usize = 1;

    // Number of seconds to wait before printing debug progress info
    const PROGRESS_INTERVAL: u64 = 30;

    // If this env var is set during extraction, the Binwalk.base_target_file symlink will
    // be deleted at the end of extraction.
    const BINWALK_RM_SYMLINK: &str = "BINWALK_RM_EXTRACTION_SYMLINK";

    // Output directory for extracted files
    let mut output_directory: Option<String> = None;

    /*
     * Maintain a queue of files waiting to be analyzed.
     * Note that ThreadPool has its own internal queue so this may seem redundant, however,
     * queuing a large number of jobs via the ThreadPool queue results in *massive* amounts
     * of unecessary memory consumption, especially when recursively analyzing many files.
     */
    let mut target_files = VecDeque::new();

    // Statistics variables; keeps track of analyzed file count and total analysis run time
    let mut file_count: usize = 0;
    let run_time = time::Instant::now();
    let mut last_progress_interval = time::Instant::now();

    // Initialize logging
    env_logger::init();

    // Process command line arguments
    let mut cliargs = cliparser::parse();

    // If --list was specified, just display a list of signatures and return
    if cliargs.list {
        display::print_signature_list(cliargs.quiet, &magic::patterns());
        return;
    }

    // Set a dummy file name when reading from stdin
    if cliargs.stdin {
        cliargs.file_name = Some(STDIN.to_string());
    }

    let mut json_logger = json::JsonLogger::new(cliargs.log);

    // If entropy analysis was requested, generate the entropy graph and return
    if cliargs.entropy {
        display::print_plain(cliargs.quiet, "Calculating file entropy...");

        if let Ok(entropy_results) =
            entropy::plot(cliargs.file_name.unwrap(), cliargs.stdin, cliargs.png)
        {
            // Log entropy results to JSON file, if requested
            json_logger.log(json::JSONType::Entropy(entropy_results.clone()));
            json_logger.close();

            display::println_plain(cliargs.quiet, "done.");
        } else {
            panic!("Entropy analysis failed!");
        }

        return;
    }

    // If extraction or data carving was requested, we need to initialize the output directory
    if cliargs.extract || cliargs.carve {
        output_directory = Some(cliargs.directory);
    }

    // Initialize binwalk
    let binwalker = match binwalk::Binwalk::configure(
        cliargs.file_name,
        output_directory,
        cliargs.include,
        cliargs.exclude,
        None,
        cliargs.search_all,
    ) {
        Err(e) => {
            panic!("Binwalk initialization failed: {}", e.message);
        }
        Ok(bw) => bw,
    };

    // If the user specified --threads, honor that request; else, auto-detect available parallelism
    let available_workers = cliargs.threads.unwrap_or_else(|| {
        // Get CPU core info
        match thread::available_parallelism() {
            // In case of error use the default
            Err(e) => {
                error!("Failed to retrieve CPU core info: {e}");
                DEFAULT_WORKER_COUNT
            }
            Ok(coreinfo) => coreinfo.get(),
        }
    });

    // Sanity check the number of available worker threads
    if available_workers < 1 {
        panic!("No available worker threads!");
    }

    // Initialize thread pool
    debug!(
        "Initializing thread pool with {} workers",
        available_workers
    );
    let workers = ThreadPool::new(available_workers);
    let (worker_tx, worker_rx) = mpsc::channel();

    /*
     * Set a custom panic handler.
     * This ensures that when any thread panics, the default panic handler will be invoked
     * _and_ the entire process will exit with an error code.
     */
    let default_panic_handler = panic::take_hook();
    panic::set_hook(Box::new(move |panic_info| {
        default_panic_handler(panic_info);
        process::exit(-1);
    }));

    debug!(
        "Queuing initial target file: {}",
        binwalker.base_target_file
    );

    // Queue the initial file path
    target_files.insert(target_files.len(), binwalker.base_target_file.clone());

    /*
     * Main loop.
     * Loop until all pending thread jobs are complete and there are no more files in the queue.
     */
    while !target_files.is_empty() || workers.active_count() > 0 {
        // If there are files waiting to be analyzed and there is at least one free thread in the pool
        if !target_files.is_empty() && workers.active_count() < workers.max_count() {
            // Get the next file path from the target_files queue
            let target_file = target_files
                .pop_front()
                .expect("Failed to retrieve next file from the queue");

            // Spawn a new worker for the new file
            spawn_worker(
                &workers,
                binwalker.clone(),
                target_file,
                cliargs.stdin && file_count == 0,
                cliargs.extract,
                cliargs.carve,
                worker_tx.clone(),
            );
        }

        // Don't spin CPU cycles if there is no backlog of files to analyze
        if target_files.is_empty() {
            let sleep_time = time::Duration::from_millis(1);
            thread::sleep(sleep_time);
        }

        // Some debug info on analysis progress
        if last_progress_interval.elapsed().as_secs() >= PROGRESS_INTERVAL {
            info!(
                "Status: active worker threads: {}/{}, files waiting in queue: {}",
                workers.active_count(),
                workers.max_count(),
                target_files.len()
            );
            last_progress_interval = time::Instant::now();
        }

        // Get response from a worker thread, if any
        if let Ok(results) = worker_rx.try_recv() {
            // Keep a tally of how many files have been analyzed
            file_count += 1;

            // Log analysis results to JSON file
            json_logger.log(json::JSONType::Analysis(results.clone()));

            // Nothing found? Nothing else to do for this file.
            if results.file_map.is_empty() {
                debug!("Found no results for file {}", results.file_path);
                continue;
            }

            // Print analysis results to screen
            if should_display(&results, file_count, cliargs.verbose) {
                display::print_analysis_results(cliargs.quiet, cliargs.extract, &results);
            }

            // If running recursively, add extraction results to list of files to analyze
            if cliargs.matryoshka {
                for (_signature_id, extraction_result) in results.extractions.into_iter() {
                    if !extraction_result.do_not_recurse {
                        for file_path in extractors::common::get_extracted_files(
                            &extraction_result.output_directory,
                        ) {
                            debug!("Queuing {file_path} for analysis");
                            target_files.insert(target_files.len(), file_path.clone());
                        }
                    }
                }
            }
        }
    }

    json_logger.close();

    // If BINWALK_RM_SYMLINK env var was set, delete the base_target_file symlink
    if (cliargs.carve || cliargs.extract) && std::env::var(BINWALK_RM_SYMLINK).is_ok() {
        if let Err(e) = std::fs::remove_file(&binwalker.base_target_file) {
            error!(
                "Request to remove extraction symlink file {} failed: {}",
                binwalker.base_target_file, e
            );
        }
    }

    // All done, show some basic statistics
    display::print_stats(
        cliargs.quiet,
        run_time,
        file_count,
        binwalker.signature_count,
        binwalker.pattern_count,
    );
}

/// Returns true if the specified results should be displayed to screen
fn should_display(results: &AnalysisResults, file_count: usize, verbose: bool) -> bool {
    let mut display_results: bool = false;

    /*
     * For brevity, when analyzing more than one file only display subsequent files whose results
     * contain signatures that we always want displayed, or which contain extractable signatures.
     * This can be overridden with the --verbose command line flag.
     */
    if file_count == 1 || verbose || !results.extractions.is_empty() {
        display_results = true;
    } else {
        for signature in &results.file_map {
            if signature.always_display {
                display_results = true;
                break;
            }
        }
    }

    display_results
}

/// Spawn a worker thread to analyze a file
fn spawn_worker(
    pool: &ThreadPool,
    bw: binwalk::Binwalk,
    target_file: String,
    stdin: bool,
    do_extraction: bool,
    do_carve: bool,
    worker_tx: mpsc::Sender<AnalysisResults>,
) {
    pool.execute(move || {
        // Read in file data
        let file_data = match common::read_input(&target_file, stdin) {
            Err(_) => {
                error!("Failed to read {} data", target_file);
                b"".to_vec()
            }
            Ok(data) => data,
        };

        // Analyze target file, with extraction, if specified
        let results = bw.analyze_buf(&file_data, &target_file, do_extraction);

        // If data carving was requested as part of extraction, carve analysis results to disk
        if do_carve {
            let carve_count = carve_file_map(&file_data, &results);
            info!(
                "Carved {} data blocks to disk from {}",
                carve_count, target_file
            );
        }

        // Report file results back to main thread
        if let Err(e) = worker_tx.send(results) {
            panic!(
                "Worker thread for {target_file} failed to send results back to main thread: {e}"
            );
        }
    });
}

/// Carve signatures identified during analysis to separate files on disk.
/// Returns the number of carved files created.
/// Note that unknown blocks of file data are also carved to disk, so the number of files
/// created may be larger than the number of results defined in results.file_map.
fn carve_file_map(file_data: &[u8], results: &binwalk::AnalysisResults) -> usize {
    let mut carve_count: usize = 0;
    let mut last_known_offset: usize = 0;
    let mut unknown_bytes: Vec<(usize, usize)> = Vec::new();

    // No results, don't do anything
    if !results.file_map.is_empty() {
        // Loop through all identified signatures in the file
        for signature_result in &results.file_map {
            // If there is data between the last signature and this signature, it is some chunk of unknown data
            if signature_result.offset > last_known_offset {
                unknown_bytes.push((
                    last_known_offset,
                    signature_result.offset - last_known_offset,
                ));
            }

            // Carve this signature's data to disk
            if carve_file_data_to_disk(
                &results.file_path,
                file_data,
                &signature_result.name,
                signature_result.offset,
                signature_result.size,
            ) {
                carve_count += 1;
            }

            // Update the last known offset to the end of this signature's data
            last_known_offset = signature_result.offset + signature_result.size;
        }

        // Calculate the size of any remaining data from the end of the last signature to EOF
        let remaining_data = file_data.len() - last_known_offset;

        // Add any remaining unknown data to the unknown_bytes list
        if remaining_data > 0 {
            unknown_bytes.push((last_known_offset, remaining_data));
        }

        // All known signature data has been carved to disk, now carve any unknown blocks of data to disk
        for (offset, size) in unknown_bytes {
            if carve_file_data_to_disk(&results.file_path, file_data, "unknown", offset, size) {
                carve_count += 1;
            }
        }
    }

    carve_count
}

/// Carves a block of file data to a new file on disk
fn carve_file_data_to_disk(
    source_file_path: &str,
    file_data: &[u8],
    name: &str,
    offset: usize,
    size: usize,
) -> bool {
    let chroot = extractors::common::Chroot::new(None);

    // Carved file path will be: <source file path>_<offset>_<name>.raw
    let carved_file_path = format!("{}_{}_{}.raw", source_file_path, offset, name,);

    debug!("Carving {}", carved_file_path);

    // Carve the data to disk
    if !chroot.carve_file(&carved_file_path, file_data, offset, size) {
        error!(
            "Failed to carve {} [{:#X}..{:#X}] to disk",
            carved_file_path,
            offset,
            offset + size,
        );
        return false;
    }

    true
}
