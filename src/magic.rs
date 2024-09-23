use crate::extractors;
use crate::signatures;

/*
 * Returns a list of all supported signatures, including their "magic" byte patterns and parser functions.
 */
pub fn patterns() -> Vec<signatures::common::Signature> {
    let mut binary_signatures: Vec<signatures::common::Signature> = vec![];

    // gzip
    binary_signatures.push(signatures::common::Signature {
        name: "gzip".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::gzip::gzip_magic(),
        parser: signatures::gzip::gzip_parser,
        description: signatures::gzip::DESCRIPTION.to_string(),
        extractor: Some(extractors::gzip::gzip_extractor()),
    });

    // .deb
    binary_signatures.push(signatures::common::Signature {
        name: "deb".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::deb::deb_magic(),
        parser: signatures::deb::deb_parser,
        description: signatures::deb::DESCRIPTION.to_string(),
        extractor: None,
    });

    // 7-zip
    binary_signatures.push(signatures::common::Signature {
        name: "7zip".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::sevenzip::sevenzip_magic(),
        parser: signatures::sevenzip::sevenzip_parser,
        description: signatures::sevenzip::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // xz
    binary_signatures.push(signatures::common::Signature {
        name: "xz".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::xz::xz_magic(),
        parser: signatures::xz::xz_parser,
        description: signatures::xz::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // tarball
    binary_signatures.push(signatures::common::Signature {
        name: "tarball".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::tarball::tarball_magic(),
        parser: signatures::tarball::tarball_parser,
        description: signatures::tarball::DESCRIPTION.to_string(),
        extractor: Some(extractors::tarball::tarball_extractor()),
    });

    // squashfs
    binary_signatures.push(signatures::common::Signature {
        name: "squashfs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::squashfs::squashfs_magic(),
        parser: signatures::squashfs::squashfs_parser,
        description: signatures::squashfs::DESCRIPTION.to_string(),
        extractor: Some(extractors::squashfs::squashfs_extractor()),
    });

    // dlob
    binary_signatures.push(signatures::common::Signature {
        name: "dlob".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::dlob::dlob_magic(),
        parser: signatures::dlob::dlob_parser,
        description: signatures::dlob::DESCRIPTION.to_string(),
        extractor: None,
    });

    // lzma
    binary_signatures.push(signatures::common::Signature {
        name: "lzma".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::lzma::lzma_magic(),
        parser: signatures::lzma::lzma_parser,
        description: signatures::lzma::DESCRIPTION.to_string(),
        //extractor: Some(extractors::sevenzip::sevenzip_extractor()),
        extractor: Some(extractors::lzma::lzma_extractor()),
    });

    // bzip2
    binary_signatures.push(signatures::common::Signature {
        name: "bzip2".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::bzip2::bzip2_magic(),
        parser: signatures::bzip2::bzip2_parser,
        description: signatures::bzip2::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // uimage
    binary_signatures.push(signatures::common::Signature {
        name: "uimage".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::uimage::uimage_magic(),
        parser: signatures::uimage::uimage_parser,
        description: signatures::uimage::DESCRIPTION.to_string(),
        extractor: None,
    });

    // packimg header
    binary_signatures.push(signatures::common::Signature {
        name: "packimg".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::packimg::packimg_magic(),
        parser: signatures::packimg::packimg_parser,
        description: signatures::packimg::DESCRIPTION.to_string(),
        extractor: None,
    });

    // crc32 constants
    binary_signatures.push(signatures::common::Signature {
        name: "crc32".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::hashes::crc32_magic(),
        parser: signatures::hashes::crc32_parser,
        description: signatures::hashes::CRC32_DESCRIPTION.to_string(),
        extractor: None,
    });

    // sha256 constants
    binary_signatures.push(signatures::common::Signature {
        name: "sha256".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::hashes::sha256_magic(),
        parser: signatures::hashes::sha256_parser,
        description: signatures::hashes::SHA256_DESCRIPTION.to_string(),
        extractor: None,
    });

    // cpio
    binary_signatures.push(signatures::common::Signature {
        name: "cpio".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::cpio::cpio_magic(),
        parser: signatures::cpio::cpio_parser,
        description: signatures::cpio::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // iso9660 primary volume
    binary_signatures.push(signatures::common::Signature {
        name: "iso9660".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::iso9660::iso_magic(),
        parser: signatures::iso9660::iso_parser,
        description: signatures::iso9660::DESCRIPTION.to_string(),
        extractor: Some(extractors::tsk::tsk_extractor()),
    });

    // linux kernel version
    binary_signatures.push(signatures::common::Signature {
        name: "linux_kernel_version".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::linux::linux_kernel_version_magic(),
        parser: signatures::linux::linux_kernel_version_parser,
        description: signatures::linux::LINUX_KERNEL_VERSION_DESCRIPTION.to_string(),
        extractor: None,
    });

    // linux boot image
    binary_signatures.push(signatures::common::Signature {
        name: "linux_boot_image".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::linux::linux_boot_image_magic(),
        parser: signatures::linux::linux_boot_image_parser,
        description: signatures::linux::LINUX_BOOT_IMAGE_DESCRIPTION.to_string(),
        extractor: None,
    });

    // zstd
    binary_signatures.push(signatures::common::Signature {
        name: "zstd".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::zstd::zstd_magic(),
        parser: signatures::zstd::zstd_parser,
        description: signatures::zstd::DESCRIPTION.to_string(),
        extractor: Some(extractors::zstd::zstd_extractor()),
    });

    // zip
    binary_signatures.push(signatures::common::Signature {
        name: "zip".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::zip::zip_magic(),
        parser: signatures::zip::zip_parser,
        description: signatures::zip::DESCRIPTION.to_string(),
        extractor: Some(extractors::zip::zip_extractor()),
    });

    // Intel PCH ROM
    binary_signatures.push(signatures::common::Signature {
        name: "pchrom".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::pchrom::pch_rom_magic(),
        parser: signatures::pchrom::pch_rom_parser,
        description: signatures::pchrom::DESCRIPTION.to_string(),
        extractor: Some(extractors::uefi::uefi_extractor()),
    });

    // UEFI PI volume
    binary_signatures.push(signatures::common::Signature {
        name: "ueif_pi_volume".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::uefi::uefi_volume_magic(),
        parser: signatures::uefi::uefi_volume_parser,
        description: signatures::uefi::VOLUME_DESCRIPTION.to_string(),
        extractor: Some(extractors::uefi::uefi_extractor()),
    });

    // UEFI capsule image
    binary_signatures.push(signatures::common::Signature {
        name: "uefi_capsule".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::uefi::uefi_capsule_magic(),
        parser: signatures::uefi::uefi_capsule_parser,
        description: signatures::uefi::CAPSULE_DESCRIPTION.to_string(),
        extractor: Some(extractors::uefi::uefi_extractor()),
    });

    // PDF document
    binary_signatures.push(signatures::common::Signature {
        name: "pdf".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::pdf::pdf_magic(),
        parser: signatures::pdf::pdf_parser,
        description: signatures::pdf::DESCRIPTION.to_string(),
        extractor: None,
    });

    // ELF
    binary_signatures.push(signatures::common::Signature {
        name: "elf".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::elf::elf_magic(),
        parser: signatures::elf::elf_parser,
        description: signatures::elf::DESCRIPTION.to_string(),
        extractor: None,
    });

    // CramFS
    binary_signatures.push(signatures::common::Signature {
        name: "cramfs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::cramfs::cramfs_magic(),
        parser: signatures::cramfs::cramfs_parser,
        description: signatures::cramfs::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // QNX IFS
    // TODO: The signature and extractor are untested. Need a sample IFS image.
    binary_signatures.push(signatures::common::Signature {
        name: "qnx_ifs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::qnx::qnx_ifs_magic(),
        parser: signatures::qnx::qnx_ifs_parser,
        description: signatures::qnx::IFS_DESCRIPTION.to_string(),
        extractor: Some(extractors::dumpifs::dumpifs_extractor()),
    });

    // RomFS
    binary_signatures.push(signatures::common::Signature {
        name: "romfs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::romfs::romfs_magic(),
        parser: signatures::romfs::romfs_parser,
        description: signatures::romfs::DESCRIPTION.to_string(),
        extractor: Some(extractors::romfs::romfs_extractor()),
    });

    // EXT
    binary_signatures.push(signatures::common::Signature {
        name: "ext".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::ext::ext_magic(),
        parser: signatures::ext::ext_parser,
        description: signatures::ext::DESCRIPTION.to_string(),
        extractor: Some(extractors::tsk::tsk_extractor()),
    });

    // CAB archive
    binary_signatures.push(signatures::common::Signature {
        name: "cab".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::cab::cab_magic(),
        parser: signatures::cab::cab_parser,
        description: signatures::cab::DESCRIPTION.to_string(),
        extractor: Some(extractors::cab::cab_extractor()),
    });

    // JFFS2
    binary_signatures.push(signatures::common::Signature {
        name: "jffs2".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::jffs2::jffs2_magic(),
        parser: signatures::jffs2::jffs2_parser,
        description: signatures::jffs2::DESCRIPTION.to_string(),
        extractor: Some(extractors::jffs2::jffs2_extractor()),
    });

    // YAFFS
    binary_signatures.push(signatures::common::Signature {
        name: "yaffs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::yaffs::yaffs_magic(),
        parser: signatures::yaffs::yaffs_parser,
        description: signatures::yaffs::DESCRIPTION.to_string(),
        extractor: Some(extractors::tsk::tsk_extractor()),
    });

    // lz4
    binary_signatures.push(signatures::common::Signature {
        name: "lz4".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::lz4::lz4_magic(),
        parser: signatures::lz4::lz4_parser,
        description: signatures::lz4::DESCRIPTION.to_string(),
        extractor: Some(extractors::lz4::lz4_extractor()),
    });

    // lzop
    binary_signatures.push(signatures::common::Signature {
        name: "lzop".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::lzop::lzop_magic(),
        parser: signatures::lzop::lzop_parser,
        description: signatures::lzop::DESCRIPTION.to_string(),
        extractor: Some(extractors::lzop::lzop_extractor()),
    });

    // lzop
    binary_signatures.push(signatures::common::Signature {
        name: "pe".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::pe::pe_magic(),
        parser: signatures::pe::pe_parser,
        description: signatures::pe::DESCRIPTION.to_string(),
        extractor: None,
    });

    // zlib
    binary_signatures.push(signatures::common::Signature {
        name: "zlib".to_string(),
        // The magic bytes for this signature are only 2 bytes, only match on the beginning of a file
        short: true,
        magic_offset: 0,
        always_display: false,
        magic: signatures::zlib::zlib_magic(),
        parser: signatures::zlib::zlib_parser,
        description: signatures::zlib::DESCRIPTION.to_string(),
        extractor: Some(extractors::zlib::zlib_extractor()),
    });

    // gpg signed data
    binary_signatures.push(signatures::common::Signature {
        name: "gpg_signed".to_string(),
        // The magic bytes for this signature are only 2 bytes, only match on the beginning of a file
        short: true,
        magic_offset: 0,
        always_display: false,
        magic: signatures::gpg::gpg_signed_magic(),
        parser: signatures::gpg::gpg_signed_parser,
        description: signatures::gpg::GPG_SIGNED_DESCRIPTION.to_string(),
        extractor: Some(extractors::zlib::zlib_extractor()),
    });

    // pem certificates
    binary_signatures.push(signatures::common::Signature {
        name: "pem_certificate".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::pem::pem_certificate_magic(),
        parser: signatures::pem::pem_parser,
        description: signatures::pem::PEM_CERTIFICATE_DESCRIPTION.to_string(),
        extractor: Some(extractors::pem::pem_certificate_extractor()),
    });

    // pem public keys
    binary_signatures.push(signatures::common::Signature {
        name: "pem_public_key".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::pem::pem_public_key_magic(),
        parser: signatures::pem::pem_parser,
        description: signatures::pem::PEM_PUBLIC_KEY_DESCRIPTION.to_string(),
        extractor: Some(extractors::pem::pem_key_extractor()),
    });

    // pem private keys
    binary_signatures.push(signatures::common::Signature {
        name: "pem_private_key".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::pem::pem_private_key_magic(),
        parser: signatures::pem::pem_parser,
        description: signatures::pem::PEM_PRIVATE_KEY_DESCRIPTION.to_string(),
        extractor: Some(extractors::pem::pem_key_extractor()),
    });

    // netgear chk
    binary_signatures.push(signatures::common::Signature {
        name: "chk".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::chk::chk_magic(),
        parser: signatures::chk::chk_parser,
        description: signatures::chk::DESCRIPTION.to_string(),
        extractor: None,
    });

    // trx
    binary_signatures.push(signatures::common::Signature {
        name: "trx".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::trx::trx_magic(),
        parser: signatures::trx::trx_parser,
        description: signatures::trx::DESCRIPTION.to_string(),
        extractor: None,
    });

    // Motorola S-record
    binary_signatures.push(signatures::common::Signature {
        name: "srecord".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::srec::srec_magic(),
        parser: signatures::srec::srec_parser,
        description: signatures::srec::SREC_DESCRIPTION.to_string(),
        extractor: Some(extractors::srec::srec_extractor()),
    });

    // Motorola S-record (generic)
    binary_signatures.push(signatures::common::Signature {
        name: "srecord_generic".to_string(),
        short: true,
        magic_offset: 0,
        always_display: false,
        magic: signatures::srec::srec_short_magic(),
        parser: signatures::srec::srec_parser,
        description: signatures::srec::SREC_SHORT_DESCRIPTION.to_string(),
        extractor: Some(extractors::srec::srec_extractor()),
    });

    // Android sparse
    binary_signatures.push(signatures::common::Signature {
        name: "android_sparse".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::androidsparse::android_sparse_magic(),
        parser: signatures::androidsparse::android_sparse_parser,
        description: signatures::androidsparse::DESCRIPTION.to_string(),
        extractor: Some(extractors::androidsparse::android_sparse_extractor()),
    });

    // device tree blob
    binary_signatures.push(signatures::common::Signature {
        name: "dtb".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::dtb::dtb_magic(),
        parser: signatures::dtb::dtb_parser,
        description: signatures::dtb::DESCRIPTION.to_string(),
        extractor: Some(extractors::dtb::dtb_extractor()),
    });

    // ubi
    binary_signatures.push(signatures::common::Signature {
        name: "ubi".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::ubi::ubi_magic(),
        parser: signatures::ubi::ubi_parser,
        description: signatures::ubi::UBI_IMAGE_DESCRIPTION.to_string(),
        extractor: Some(extractors::ubi::ubi_extractor()),
    });

    // ubifs
    binary_signatures.push(signatures::common::Signature {
        name: "ubifs".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::ubi::ubifs_magic(),
        parser: signatures::ubi::ubifs_parser,
        description: signatures::ubi::UBI_FS_DESCRIPTION.to_string(),
        extractor: Some(extractors::ubi::ubifs_extractor()),
    });

    // cfe bootloader
    binary_signatures.push(signatures::common::Signature {
        name: "cfe".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::cfe::cfe_magic(),
        parser: signatures::cfe::cfe_parser,
        description: signatures::cfe::DESCRIPTION.to_string(),
        extractor: None,
    });

    // SEAMA firmware header
    binary_signatures.push(signatures::common::Signature {
        name: "seama".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::seama::seama_magic(),
        parser: signatures::seama::seama_parser,
        description: signatures::seama::DESCRIPTION.to_string(),
        extractor: None,
    });

    // compress'd
    binary_signatures.push(signatures::common::Signature {
        name: "compressd".to_string(),
        short: true,
        magic_offset: 0,
        always_display: false,
        magic: signatures::compressd::compressd_magic(),
        parser: signatures::compressd::compressd_parser,
        description: signatures::compressd::DESCRIPTION.to_string(),
        extractor: Some(extractors::sevenzip::sevenzip_extractor()),
    });

    // rar archive
    binary_signatures.push(signatures::common::Signature {
        name: "rar".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::rar::rar_magic(),
        parser: signatures::rar::rar_parser,
        description: signatures::rar::DESCRIPTION.to_string(),
        extractor: Some(extractors::rar::rar_extractor()),
    });

    // PNG image
    binary_signatures.push(signatures::common::Signature {
        name: "png".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::png::png_magic(),
        parser: signatures::png::png_parser,
        description: signatures::png::DESCRIPTION.to_string(),
        extractor: Some(extractors::png::png_extractor()),
    });

    // JPEG image
    binary_signatures.push(signatures::common::Signature {
        name: "jpeg".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::jpeg::jpeg_magic(),
        parser: signatures::jpeg::jpeg_parser,
        description: signatures::jpeg::DESCRIPTION.to_string(),
        extractor: Some(extractors::jpeg::jpeg_extractor()),
    });

    // arcadyan obfuscated lzma
    binary_signatures.push(signatures::common::Signature {
        name: "arcadyan".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::arcadyan::obfuscated_lzma_magic(),
        parser: signatures::arcadyan::obfuscated_lzma_parser,
        description: signatures::arcadyan::DESCRIPTION.to_string(),
        extractor: Some(extractors::arcadyan::obfuscated_lzma_extractor()),
    });

    // copyright text
    binary_signatures.push(signatures::common::Signature {
        name: "copyright".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::copyright::copyright_magic(),
        parser: signatures::copyright::copyright_parser,
        description: signatures::copyright::DESCRIPTION.to_string(),
        extractor: None,
    });

    // WIND kernel version
    binary_signatures.push(signatures::common::Signature {
        name: "wind_kernel".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::vxworks::wind_kernel_magic(),
        parser: signatures::vxworks::wind_kernel_parser,
        description: signatures::vxworks::WIND_KERNEL_DESCRIPTION.to_string(),
        extractor: None,
    });

    // vxworks symbol table
    binary_signatures.push(signatures::common::Signature {
        name: "vxworks_symtab".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::vxworks::symbol_table_magic(),
        parser: signatures::vxworks::symbol_table_parser,
        description: signatures::vxworks::SYMTAB_DESCRIPTION.to_string(),
        extractor: Some(extractors::vxworks::vxworks_symtab_extractor()),
    });

    // ecos mips exception handler
    binary_signatures.push(signatures::common::Signature {
        name: "ecos".to_string(),
        short: false,
        magic_offset: 0,
        always_display: true,
        magic: signatures::ecos::exception_handler_magic(),
        parser: signatures::ecos::exception_handler_parser,
        description: signatures::ecos::EXCEPTION_HANDLER_DESCRIPTION.to_string(),
        extractor: None,
    });

    // dmg
    binary_signatures.push(signatures::common::Signature {
        name: "dmg".to_string(),
        short: false,
        magic_offset: 0,
        always_display: false,
        magic: signatures::dmg::dmg_magic(),
        parser: signatures::dmg::dmg_parser,
        description: signatures::dmg::DESCRIPTION.to_string(),
        extractor: Some(extractors::dmg::dmg_extractor()),
    });

    return binary_signatures;
}
