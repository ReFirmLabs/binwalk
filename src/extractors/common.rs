use crate::signatures::common::SignatureResult;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::path;
use std::process;
use walkdir::WalkDir;

#[cfg(windows)]
use std::os::windows;

#[cfg(unix)]
use std::os::unix;
#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

/// This contstant in command line arguments will be replaced with the path to the input file
pub const SOURCE_FILE_PLACEHOLDER: &str = "%e";

/// Return value of InternalExtractor upon error
#[derive(Debug, Clone)]
pub struct ExtractionError;

/// Built-in internal extractors must provide a function conforming to this definition.
/// Arguments: file_data, offset, output_directory.
pub type InternalExtractor = fn(&[u8], usize, Option<&String>) -> ExtractionResult;

/// Enum to define either an Internal or External extractor type
#[derive(Debug, Default, Clone, Eq, PartialEq, Ord, PartialOrd)]
pub enum ExtractorType {
    External(String),
    Internal(InternalExtractor),
    #[default]
    None,
}

/// Describes extractors, both external and internal
#[derive(Debug, Clone, Default, PartialEq, Eq, PartialOrd, Ord)]
pub struct Extractor {
    /// External command or internal function to execute
    pub utility: ExtractorType,
    /// File extension expected by an external command
    pub extension: String,
    /// Arguments to pass to the external command
    pub arguments: Vec<String>,
    /// A list of successful exit codes for the external command
    pub exit_codes: Vec<i32>,
    /// Set to true to disable recursion into this extractor's extracted files
    pub do_not_recurse: bool,
}

/// Stores information about a completed extraction
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExtractionResult {
    /// Size of the data consumed during extraction, if known; should be populated by the constructor
    pub size: Option<usize>,
    /// Extractor success status; should be populated by the constructor
    pub success: bool,
    /// Extractor name, automatically populated by extractors::common::execute
    pub extractor: String,
    /// Set to true to disable recursion into this extractor's extracted files.
    /// Automatically populated with the corresponding Extractor.do_not_recurse field by extractors::common::execute.
    pub do_not_recurse: bool,
    /// The output directory where the extractor dropped its files, automatically populated by extractors::common::execute
    pub output_directory: String,
}

/// Stores information about external extractor processes. For internal use only.
#[derive(Debug)]
pub struct ProcInfo {
    pub child: process::Child,
    pub exit_codes: Vec<i32>,
    pub carved_file: String,
}

/// Provides chroot-like functionality for internal extractors
#[derive(Debug, Default, Clone)]
pub struct Chroot {
    /// The chroot directory passed to Chroot::new
    pub chroot_directory: String,
}

impl Chroot {
    /// Create a new chrooted instance. All file paths will be effectively chrooted in the specified directory path.
    /// The chroot directory path will be created if it does not already exist.
    ///
    /// If no directory path is specified, the chroot directory will be `/`.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::extractors::common::Chroot;
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot_directory = "/tmp/foobar".to_string();
    /// let chroot = Chroot::new(Some(&chroot_directory));
    ///
    /// assert_eq!(chroot.chroot_directory, "/tmp/foobar");
    /// assert_eq!(std::path::Path::new("/tmp/foobar").exists(), true);
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// ```
    pub fn new(chroot_directory: Option<&String>) -> Chroot {
        let mut chroot_instance = Chroot {
            ..Default::default()
        };

        match chroot_directory {
            None => {
                // Default path is '/'
                chroot_instance.chroot_directory = path::MAIN_SEPARATOR.to_string();
            }
            Some(chroot_dir) => {
                // Attempt to ensure that the specified path is absolute. If this fails, just use the path as given.
                match path::absolute(chroot_dir) {
                    Ok(pathbuf) => {
                        chroot_instance.chroot_directory = pathbuf.display().to_string();
                    }
                    Err(_) => {
                        chroot_instance.chroot_directory = chroot_dir.clone();
                    }
                }
            }
        }

        // Create the chroot directory if it does not exist
        if !path::Path::new(&chroot_instance.chroot_directory).exists() {
            match fs::create_dir_all(&chroot_instance.chroot_directory) {
                Ok(_) => {
                    debug!(
                        "Created new chroot directory {}",
                        chroot_instance.chroot_directory
                    );
                }
                Err(e) => {
                    error!(
                        "Failed to create chroot directory {}: {}",
                        chroot_instance.chroot_directory, e
                    );
                }
            }
        }

        chroot_instance
    }

    /// Joins two paths, ensuring that the final path does not traverse outside of the chroot directory.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_directory = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_directory));
    ///
    /// let path1 = chroot.safe_path_join("/etc", "passwd");
    /// let path2 = chroot.safe_path_join("/etc", "../../passwd");
    /// let path3 = chroot.safe_path_join("../../../etc", "/passwd");
    /// let path4 = chroot.safe_path_join("/tmp/foobar/", "/etc/passwd");
    ///
    /// assert_eq!(path1, "/tmp/foobar/etc/passwd");
    /// assert_eq!(path2, "/tmp/foobar/passwd");
    /// assert_eq!(path3, "/tmp/foobar/etc/passwd");
    /// assert_eq!(path4, "/tmp/foobar/etc/passwd");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// ```
    pub fn safe_path_join(&self, path1: impl Into<String>, path2: impl Into<String>) -> String {
        // Join and sanitize both paths; retain the leading '/' (if there is one)
        let mut joined_path: String = self.sanitize_path(
            &format!("{}{}{}", path1.into(), path::MAIN_SEPARATOR, path2.into()),
            true,
        );

        // If the joined path does not start with the chroot directory,
        // prepend the chroot directory to the final joined path.
        // on Windows: If no chroot directory is specified, skip the operation
        if cfg!(windows) && self.chroot_directory == path::MAIN_SEPARATOR.to_string() {
            // do nothing and skip
        } else if !joined_path.starts_with(&self.chroot_directory) {
            joined_path = format!(
                "{}{}{}",
                self.chroot_directory,
                path::MAIN_SEPARATOR,
                joined_path
            );
        }

        self.strip_double_slash(&joined_path)
    }

    /// Given a file path, returns a sanitized path that is chrooted inside the specified chroot directory.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar/".to_string();
    ///
    /// let chroot = Chroot::new(Some(&chroot_dir));
    /// let path = chroot.chrooted_path("test.txt");
    ///
    /// assert_eq!(path, "/tmp/foobar/test.txt");
    /// ```
    pub fn chrooted_path(&self, file_path: impl Into<String>) -> String {
        self.safe_path_join(file_path, "".to_string())
    }

    /// Creates a regular file in the chrooted directory and writes the provided data to it.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_213_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    /// let file_data: &[u8] = b"foobar";
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_file("created_file.txt", file_data), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/created_file.txt")?, "foobar");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_213_0(); }
    /// ```
    pub fn create_file(&self, file_path: impl Into<String>, file_data: &[u8]) -> bool {
        let safe_file_path: String = self.chrooted_path(file_path);

        if !path::Path::new(&safe_file_path).exists() {
            match fs::write(safe_file_path.clone(), file_data) {
                Ok(_) => {
                    return true;
                }
                Err(e) => {
                    error!("Failed to write data to {}: {}", safe_file_path, e);
                }
            }
        } else {
            error!(
                "Failed to create file {}: path already exists",
                safe_file_path
            );
        }

        false
    }

    /// Carve data and write it to a new file.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_255_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    /// let file_data_with_trailing_junk: &[u8] = b"foobarJUNK";
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.carve_file("carved_file.txt", file_data_with_trailing_junk, 0, 6), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/carved_file.txt")?, "foobar");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// } _doctest_main_src_extractors_common_rs_255_0(); }
    /// ```
    pub fn carve_file(
        &self,
        file_path: impl Into<String>,
        data: &[u8],
        start: usize,
        size: usize,
    ) -> bool {
        let mut retval: bool = false;

        if let Some(file_data) = data.get(start..start + size) {
            retval = self.create_file(file_path, file_data);
        } else {
            error!(
                "Failed to create file {}: data offset/size are invalid",
                file_path.into()
            );
        }

        retval
    }

    /// Creates a device file in the chroot directory.
    ///
    /// Note that this does *not* create a real device file, just a regular file containing the device file info.
    fn create_device(
        &self,
        file_path: impl Into<String>,
        device_type: &str,
        major: usize,
        minor: usize,
    ) -> bool {
        let device_file_contents: String = format!("{} {} {}", device_type, major, minor);
        self.create_file(file_path, &device_file_contents.clone().into_bytes())
    }

    /// Creates a character device file in the chroot directory.
    ///
    /// Note that this does *not* create a real character device, just a regular file containing the text `c <major> <minor>`.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_312_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    /// let dev_major: usize = 1;
    /// let dev_minor: usize = 2;
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_character_device("char_device", dev_major, dev_minor), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/char_device")?, "c 1 2");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_312_0(); }
    /// ```
    pub fn create_character_device(
        &self,
        file_path: impl Into<String>,
        major: usize,
        minor: usize,
    ) -> bool {
        self.create_device(file_path, "c", major, minor)
    }

    /// Creates a block device file in the chroot directory.
    ///
    /// Note that this does *not* create a real block device, just a regular file containing the text `b <major> <minor>`.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_345_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    /// let dev_major: usize = 1;
    /// let dev_minor: usize = 2;
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_block_device("block_device", dev_major, dev_minor), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/block_device")?, "b 1 2");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_345_0(); }
    /// ```
    pub fn create_block_device(
        &self,
        file_path: impl Into<String>,
        major: usize,
        minor: usize,
    ) -> bool {
        self.create_device(file_path, "b", major, minor)
    }

    /// Creates a fifo file in the chroot directory.
    ///
    /// Note that this does *not* create a real fifo, just a regular file containing the text `fifo`.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_377_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_fifo("fifo_file"), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/fifo_file")?, "fifo");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_377_0(); }
    /// ```
    pub fn create_fifo(&self, file_path: impl Into<String>) -> bool {
        self.create_file(file_path, b"fifo")
    }

    /// Creates a socket file in the chroot directory.
    ///
    /// Note that this does *not* create a real socket, just a regular file containing the text `socket`.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_401_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_socket("socket_file"), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/socket_file")?, "socket");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_401_0(); }
    /// ```
    pub fn create_socket(&self, file_path: impl Into<String>) -> bool {
        self.create_file(file_path, b"socket")
    }

    /// Append the provided data to the specified file in the chroot directory.
    ///
    /// If the specified file does not exist, it will be created.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_426_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    /// let my_file_data: &[u8] = b"foobar";
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.append_to_file("append.txt", my_file_data), true);
    /// assert_eq!(std::fs::read_to_string("/tmp/foobar/append.txt")?, "foobar");
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_426_0(); }
    /// ```
    pub fn append_to_file(&self, file_path: impl Into<String>, data: &[u8]) -> bool {
        let safe_file_path: String = self.chrooted_path(file_path);

        if !self.is_symlink(&safe_file_path) {
            match fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(safe_file_path.clone())
            {
                Err(e) => {
                    error!(
                        "Failed to open file '{}' for appending: {}",
                        safe_file_path, e
                    );
                }
                Ok(mut fp) => match fp.write(data) {
                    Err(e) => {
                        error!("Failed to append to file '{}': {}", safe_file_path, e);
                    }
                    Ok(_) => {
                        return true;
                    }
                },
            }
        } else {
            error!("Attempted to append data to a symlink: {}", safe_file_path);
        }

        false
    }

    /// Creates a directory in the chroot directory.
    ///
    /// Equivalent to mkdir -p.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_directory("/usr/bin/"), true);
    /// assert_eq!(std::path::Path::new("/tmp/foobar/usr/bin").exists(), true);
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// ```
    pub fn create_directory(&self, dir_path: impl Into<String>) -> bool {
        let safe_dir_path: String = self.chrooted_path(dir_path);

        match fs::create_dir_all(safe_dir_path.clone()) {
            Ok(_) => {
                return true;
            }
            Err(e) => {
                error!("Failed to create output directory {}: {}", safe_dir_path, e);
            }
        }

        false
    }

    /// Set executable permissions on an existing file in the chroot directory.
    ///
    /// ## Example
    ///
    /// ```
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    /// chroot.create_file("runme.exe", b"AAAA");
    ///
    /// assert_eq!(chroot.make_executable("runme.exe"), true);
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// ```
    pub fn make_executable(&self, file_path: impl Into<String>) -> bool {
        // Make the file globally executable
        const UNIX_EXEC_FLAG: u32 = 1;

        let safe_file_path: String = self.chrooted_path(file_path);

        match fs::metadata(safe_file_path.clone()) {
            Err(e) => {
                error!(
                    "Failed to get permissions for file {}: {}",
                    safe_file_path, e
                );
            }
            Ok(metadata) => {
                #[cfg(unix)]
                {
                    let mut permissions = metadata.permissions();
                    let mode = permissions.mode() | UNIX_EXEC_FLAG;
                    permissions.set_mode(mode);

                    match fs::set_permissions(&safe_file_path, permissions) {
                        Err(e) => {
                            error!(
                                "Failed to set permissions for file {}: {}",
                                safe_file_path, e
                            );
                        }
                        Ok(_) => {
                            return true;
                        }
                    }
                }
                #[cfg(windows)]
                {
                    return true;
                }
            }
        }

        false
    }

    /// Creates a symbolic link in the chroot directory, named `symlink_path`, which points to `target_path`.
    ///
    /// Note that both the symlink and target paths will be sanitized to stay in the chroot directory.
    /// Both the target path will be converted into a path relative to the symlink file path.
    ///
    /// ## Example
    ///
    /// ```
    /// # fn main() { #[allow(non_snake_case)] fn _doctest_main_src_extractors_common_rs_571_0() -> Result<(), Box<dyn std::error::Error>> {
    /// use binwalk::extractors::common::Chroot;
    ///
    /// let chroot_dir = "/tmp/foobar".to_string();
    ///
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// let chroot = Chroot::new(Some(&chroot_dir));
    ///
    /// assert_eq!(chroot.create_symlink("symlink", "/"), true);
    /// assert_eq!(std::fs::canonicalize("/tmp/foobar/symlink")?.to_str(), Some("/tmp/foobar"));
    /// # std::fs::remove_dir_all("/tmp/foobar");
    /// # Ok(())
    /// # } _doctest_main_src_extractors_common_rs_571_0(); }
    /// ```
    pub fn create_symlink(
        &self,
        symlink_path: impl Into<String>,
        target_path: impl Into<String>,
    ) -> bool {
        let target = target_path.into();
        let symlink = symlink_path.into();

        // Chroot the symlink file path and create a Path object
        let safe_symlink = self.chrooted_path(&symlink);
        let safe_symlink_path = path::Path::new(&safe_symlink);

        // Normalize the symlink target path to a chrooted absolute path
        let safe_target = if target.starts_with(path::MAIN_SEPARATOR) {
            // If the target path is absolute, just chroot it inside the chroot directory
            self.chrooted_path(&target)
        } else {
            // Get the symlink file's parent directory path
            let relative_dir: String = match safe_symlink_path.parent() {
                None => {
                    // There is no parent, or parent is the root directory; assume the root directory
                    path::MAIN_SEPARATOR.to_string()
                }
                Some(parent_dir) => {
                    // Got the parent directory
                    parent_dir.display().to_string()
                }
            };

            // Join the target path with its relative directory, ensuring it does not traverse outside
            // the specified chroot directory
            self.safe_path_join(&relative_dir, &target)
        };

        // Remove the chroot directory from the target and symlink paths.
        // This results in each being an absolute path that is relative to the chroot directory,
        // e.g., '/my_chroot_dir/bin/busybox' -> '/bin/busybox'.
        //
        // Note: need at least one leading '/', so if the chroot directory is just '/', just use the string as-is.
        let mut safe_target_rel_path = if self.chroot_directory == path::MAIN_SEPARATOR.to_string()
        {
            safe_target.clone()
        } else {
            safe_target.replacen(&self.chroot_directory, "", 1)
        };

        let safe_symlink_rel_path = if self.chroot_directory == path::MAIN_SEPARATOR.to_string() {
            safe_symlink.clone()
        } else {
            safe_symlink.replacen(&self.chroot_directory, "", 1)
        };

        // Count the number of path separators (minus the leading one) and an '../' to the target
        // path for each; e.g., '/bin/busybox' -> '..//bin/busybox'.
        for _i in 0..safe_symlink_rel_path.matches(path::MAIN_SEPARATOR).count() - 1 {
            safe_target_rel_path = format!("..{}{}", path::MAIN_SEPARATOR, safe_target_rel_path);
        }

        // Add a '.' at the beginning of any paths that start with '/', e.g., '/tmp' -> './tmp'.
        if safe_target_rel_path.starts_with(path::MAIN_SEPARATOR) {
            safe_target_rel_path = format!(".{}", safe_target_rel_path);
        }

        // Replace any instances of '//' with '/'
        safe_target_rel_path = self.strip_double_slash(&safe_target_rel_path);

        // The target path is now a safely chrooted path that is relative to the symlink file path.
        // Ex:
        //
        //     Original symlink: "/my_chroot_dir/usr/sbin/ls" is a symlink to "/bin/busybox"
        //     Safe relative symlink: "/my_chroot_dir/usr/sbin/ls" is a symlink to "./../../bin/busybox"
        let safe_target_path = path::Path::new(&safe_target_rel_path);

        #[cfg(unix)]
        {
            match unix::fs::symlink(safe_target_path, safe_symlink_path) {
                Ok(_) => true,
                Err(e) => {
                    error!(
                        "Failed to create symlink from {} -> {}: {}",
                        symlink, target, e
                    );
                    false
                }
            }
        }
        #[cfg(windows)]
        {
            // let sym = match safe_target_path.is_dir() {
            //     true => windows::fs::symlink_dir(safe_target_path, safe_symlink_path),
            //     false => windows::fs::symlink_file(safe_target_path, safe_symlink_path),
            // };

            match windows::fs::symlink_dir(safe_target_path, safe_symlink_path) {
                Ok(_) => {
                    return true;
                }
                Err(e) => {
                    error!(
                        "Failed to create symlink from {} -> {}: {}",
                        symlink, target, e
                    );
                    return false;
                }
            }
        }
    }

    /// Returns true if the file path is a symlink.
    fn is_symlink(&self, file_path: &String) -> bool {
        if let Ok(metadata) = fs::symlink_metadata(file_path) {
            return metadata.file_type().is_symlink();
        }

        false
    }

    /// Replace `//` with `/`. This is for asthetics only.
    fn strip_double_slash(&self, path: &str) -> String {
        let mut stripped_path = path.to_owned();
        let single_slash = path::MAIN_SEPARATOR.to_string();
        let double_slash = format!("{}{}", single_slash, single_slash);

        while stripped_path.contains(&double_slash) {
            stripped_path = stripped_path.replace(&double_slash, &single_slash);
        }

        stripped_path
    }

    /// Interprets a given path containing '..' directories.
    fn sanitize_path(&self, file_path: &str, preserve_root_path_sep: bool) -> String {
        const DIR_TRAVERSAL: &str = "..";

        let mut exclude_indicies: Vec<usize> = vec![];
        let mut sanitized_path: String = "".to_string();

        if preserve_root_path_sep && file_path.starts_with(path::MAIN_SEPARATOR) {
            sanitized_path = path::MAIN_SEPARATOR.to_string();
        }

        // Split the file path on '/'
        let path_parts: Vec<&str> = file_path.split(path::MAIN_SEPARATOR).collect();

        // Loop through each part of the file path
        for (i, path_part) in path_parts.iter().enumerate() {
            // If this part of the path is '..', don't include it in the final sanitized path
            if *path_part == DIR_TRAVERSAL {
                exclude_indicies.push(i);
                if i > 0 {
                    // Walk backwards through the path parts until a non-excluded part is found, then mark that part for exclusion as well
                    let mut j = i - 1;
                    while j > 0 && exclude_indicies.contains(&j) {
                        j -= 1;
                    }
                    exclude_indicies.push(j);
                }
            // If this part of the path is an empty string, don't include that either (happens if the original file path has '//' in it)
            } else if path_part.is_empty() {
                exclude_indicies.push(i);
            }
        }

        // Concatenate each non-excluded part of the file path, with each part separated by '/'
        for (i, path_part) in path_parts.iter().enumerate() {
            if !exclude_indicies.contains(&i) {
                #[cfg(windows)]
                {
                    // on Windows: in the first loop run, we cannot really prepend a '\' to drive letters like 'C:'
                    if sanitized_path.is_empty() {
                        sanitized_path = path_part.to_string();
                        continue;
                    }
                }
                sanitized_path = format!("{}{}{}", sanitized_path, path::MAIN_SEPARATOR, path_part);
            }
        }

        self.strip_double_slash(&sanitized_path)
    }
}

/// Recursively walks a given directory and returns a list of regular non-zero size files in the given directory path.
#[allow(dead_code)]
pub fn get_extracted_files(directory: &String) -> Vec<String> {
    let mut regular_files: Vec<String> = vec![];

    for entry in WalkDir::new(directory).into_iter() {
        match entry {
            Err(_e) => continue,
            Ok(entry) => {
                let entry_path = entry.path();
                // Query file metadata *without* following symlinks
                match fs::symlink_metadata(entry_path) {
                    Err(_e) => continue,
                    Ok(md) => {
                        // Only interested in non-empty, regular files
                        if md.is_file() && md.len() > 0 {
                            regular_files.push(entry_path.display().to_string());
                        }
                    }
                }
            }
        }
    }

    regular_files
}

/// Executes an extractor for the provided SignatureResult.
pub fn execute(
    file_data: &[u8],
    file_path: &String,
    signature: &SignatureResult,
    extractor: &Option<Extractor>,
) -> ExtractionResult {
    let mut result = ExtractionResult {
        ..Default::default()
    };

    // Create an output directory for the extraction
    if let Ok(output_directory) = create_output_directory(file_path, signature.offset) {
        // Make sure a defalut extractor was actually defined (this function should not be called if signature.extractor is None)
        match &extractor {
            None => {
                error!(
                    "Attempted to extract {} data, but no extractor is defined!",
                    signature.name
                );
            }

            Some(default_extractor) => {
                let extractor_definition: Extractor;

                // If the signature result specified a preferred extractor, use that instead of the default signature extractor
                if let Some(preferred_extractor) = &signature.preferred_extractor {
                    extractor_definition = preferred_extractor.clone();
                } else {
                    extractor_definition = default_extractor.clone();
                }

                // Decide how to execute the extractor depending on the extractor type
                match &extractor_definition.utility {
                    ExtractorType::None => {
                        panic!("An extractor of type None is invalid!");
                    }

                    ExtractorType::Internal(func) => {
                        debug!("Executing internal {} extractor", signature.name);
                        // Run the internal extractor function
                        result = func(file_data, signature.offset, Some(&output_directory));
                        // Set the extractor name to "<signature name>_built_in"
                        result.extractor = format!("{}_built_in", signature.name);
                    }

                    ExtractorType::External(cmd) => {
                        // Spawn the external extractor command
                        match spawn(
                            file_data,
                            file_path,
                            &output_directory,
                            signature,
                            extractor_definition.clone(),
                        ) {
                            Err(e) => {
                                error!(
                                    "Failed to spawn external extractor for '{}' signature: {}",
                                    signature.name, e
                                );
                            }

                            Ok(proc_info) => {
                                // Wait for the external process to exit
                                match proc_wait(proc_info) {
                                    Err(_) => {
                                        warn!("External extractor failed!");
                                    }
                                    Ok(ext_result) => {
                                        result = ext_result;
                                        // Set the extractor name to the name of the extraction utility
                                        result.extractor = cmd.to_string();
                                    }
                                }
                            }
                        }
                    }
                }

                // Populate these ExtractionResult fields automatically for all extractors
                result.output_directory = output_directory.clone();
                result.do_not_recurse = extractor_definition.do_not_recurse;

                // If the extractor reported success, make sure it extracted something other than just an empty file
                if result.success && !was_something_extracted(&result.output_directory) {
                    result.success = false;
                    warn!("Extractor exited successfully, but no data was extracted");
                }
            }
        }

        // Clean up extractor's output directory if extraction failed
        if !result.success {
            if let Err(e) = fs::remove_dir_all(&output_directory) {
                warn!(
                    "Failed to clean up extraction directory {} after extraction failure: {}",
                    output_directory, e
                );
            }
        }
    }

    result
}

/// Spawn an external extractor process.
fn spawn(
    file_data: &[u8],
    file_path: &String,
    output_directory: &String,
    signature: &SignatureResult,
    mut extractor: Extractor,
) -> Result<ProcInfo, std::io::Error> {
    let command: String;
    let chroot = Chroot::new(None);

    // This function *only* handles execution of external extraction utilities; internal extractors must be invoked directly
    match &extractor.utility {
        ExtractorType::External(cmd) => command = cmd.clone(),
        ExtractorType::Internal(_ext) => {
            panic!("Tried to run an internal extractor as an external command!")
        }
        ExtractorType::None => panic!("An extractor command was defined, but is set to None!"),
    }

    // Carved file path will be <output directory>/<signature.name>_<hex offset>.<extractor.extension>
    let carved_file = format!(
        "{}{}{}_{:X}.{}",
        output_directory,
        path::MAIN_SEPARATOR,
        signature.name,
        signature.offset,
        extractor.extension
    );
    info!(
        "Carving data from {} {:#X}..{:#X} to {}",
        file_path,
        signature.offset,
        signature.offset + signature.size,
        carved_file
    );

    // If the entirety of the source file is this one file type, no need to carve a copy of it, just create a symlink
    if signature.offset == 0 && signature.size == file_data.len() {
        if !chroot.create_symlink(&carved_file, file_path) {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Failed to create carved file symlink",
            ));
        }
    } else {
        // Copy file data to carved file path
        if !chroot.carve_file(&carved_file, file_data, signature.offset, signature.size) {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Failed to carve data to disk",
            ));
        }
    }

    // Replace all "%e" command arguments with the path to the carved file
    for i in 0..extractor.arguments.len() {
        if extractor.arguments[i] == SOURCE_FILE_PLACEHOLDER {
            extractor.arguments[i] = carved_file.clone();
        }
    }

    info!("Spawning process {} {:?}", command, extractor.arguments);
    match process::Command::new(&command)
        .args(&extractor.arguments)
        .stdout(process::Stdio::null())
        .stderr(process::Stdio::null())
        .current_dir(output_directory)
        .spawn()
    {
        Err(e) => {
            error!(
                "Failed to execute command {}{:?}: {}",
                command, extractor.arguments, e
            );
            Err(e)
        }

        Ok(child) => {
            // If the process was spawned successfully, return some information about the process
            let proc_info = ProcInfo {
                child,
                carved_file: carved_file.clone(),
                exit_codes: extractor.exit_codes,
            };

            Ok(proc_info)
        }
    }
}

/// Waits for an extraction process to complete.
/// Returns ExtractionError if the extractor was prematurely terminated, else returns an ExtractionResult.
fn proc_wait(mut worker_info: ProcInfo) -> Result<ExtractionResult, ExtractionError> {
    // The standard exit success value is 0
    const EXIT_SUCCESS: i32 = 0;

    // Block until child process has terminated
    match worker_info.child.wait() {
        // Child was terminated from an external signal, status unknown, assume failure but do nothing else
        Err(e) => {
            error!("Failed to retreive child process status: {}", e);
            Err(ExtractionError)
        }

        // Child terminated with an exit status
        Ok(status) => {
            // Assume failure until proven otherwise
            let mut extraction_success: bool = false;

            // Clean up the carved file used as input to the extractor
            debug!("Deleting carved file {}", worker_info.carved_file);
            if let Err(e) = fs::remove_file(worker_info.carved_file.clone()) {
                warn!(
                    "Failed to remove carved file '{}': {}",
                    worker_info.carved_file, e
                );
            };

            // Check the extractor's exit status
            match status.code() {
                None => {
                    extraction_success = false;
                }

                Some(code) => {
                    // Make sure the extractor's exit code is an expected one
                    if code == EXIT_SUCCESS || worker_info.exit_codes.contains(&code) {
                        extraction_success = true;
                    } else {
                        warn!("Child process exited with unexpected code: {}", code);
                    }
                }
            }

            // Return an ExtractionResult with the appropriate success status
            Ok(ExtractionResult {
                success: extraction_success,
                ..Default::default()
            })
        }
    }
}

// Create an output directory in which to place extraction results
fn create_output_directory(file_path: &String, offset: usize) -> Result<String, std::io::Error> {
    let chroot = Chroot::new(None);

    // Output directory will be: <file_path.extracted/<hex offset>
    let output_directory = format!(
        "{}.extracted{}{:X}",
        file_path,
        path::MAIN_SEPARATOR,
        offset
    );

    // Create the output directory, equivalent of mkdir -p
    if !chroot.create_directory(&output_directory) {
        return Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            "Directory creation failed",
        ));
    }

    Ok(output_directory)
}

/// Returns true if the size of the provided extractor output directory is greater than zero.
/// Note that any intermediate/carved files must be deleted *before* calling this function.
fn was_something_extracted(output_directory: &String) -> bool {
    let output_directory_path = path::Path::new(output_directory);
    debug!("Checking output directory {} for results", output_directory);

    // Walk the output directory looking for something, anything, that isn't an empty file
    for entry in WalkDir::new(output_directory).into_iter() {
        match entry {
            Err(e) => {
                warn!("Failed to retrieve output directory entry: {}", e);
                continue;
            }
            Ok(entry) => {
                // Don't include the base output directory path itself
                if entry.path() == output_directory_path {
                    continue;
                }

                debug!("Found output file {}", entry.path().display());

                match fs::symlink_metadata(entry.path()) {
                    Err(_e) => continue,
                    Ok(md) => {
                        if md.len() > 0 {
                            return true;
                        }
                    }
                }
            }
        }
    }

    false
}
