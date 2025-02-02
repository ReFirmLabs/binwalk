use crate::structures::common::{self, StructureError};

/*
 Blob structure: from mimikatz repository.
   DWORD	dwVersion;
   GUID	guidProvider;
   DWORD	dwMasterKeyVersion;
   GUID	guidMasterKey;
   DWORD	dwFlags;

   DWORD	dwDescriptionLen;
   PWSTR	szDescription;

   ALG_ID	algCrypt;
   DWORD	dwAlgCryptLen;

   DWORD	dwSaltLen;
   PBYTE	pbSalt;

   DWORD	dwHmacKeyLen;
   PBYTE	pbHmackKey;

   ALG_ID	algHash;
   DWORD	dwAlgHashLen;

   DWORD	dwHmac2KeyLen;
   PBYTE	pbHmack2Key;

   DWORD	dwDataLen;
   PBYTE	pbData;

   DWORD	dwSignLen;
   PBYTE	pbSign;
*/

/// Struct to store DPAPI blob structure
#[derive(Debug, Default, Clone)]
pub struct DPAPIBlobHeader {
    pub header_size: usize,
    pub blob_size: usize,
    pub version: usize,
    pub provider_id: usize,
    pub master_key_version: usize,
    pub master_key_id: usize,
    pub flags: usize,
    pub description_len: usize,
    pub crypto_algorithm: usize,
    pub crypti_alg_len: usize,
    pub salt_len: usize,
    pub hmac_key_len: usize,
    pub hash_algorithm: usize,
    pub hash_alg_len: usize,
    pub hmac2_key_len: usize,
    pub data_len: usize,
    pub sign_len: usize,
}

/// Parse a DPAPI BLOB
pub fn parse_dpapi_blob_header(dpapi_blob_data: &[u8]) -> Result<DPAPIBlobHeader, StructureError> {
    let initial_dpapi_structure = vec![
        ("version", "u32"),
        ("provider_id", "u128"),
        ("master_key_version", "u32"),
        ("master_key_id", "u128"),
        ("flags", "u32"),
        ("description_len", "u32"),
    ];
    let mut offset: usize = (32 + 128 + 32 + 128 + 32 + 32) / 8;

    let mut dpapi_header = common::parse(dpapi_blob_data, &initial_dpapi_structure, "little")?;
    let description_len = dpapi_header["description_len"];

    if description_len % 2 != 0 {
        return Err(StructureError);
    }

    let utf16_vec =
        utf8_to_utf16(&dpapi_blob_data[offset..=offset + description_len]).ok_or(StructureError)?;
    let desc = String::from_utf16(&utf16_vec).map_err(|_| StructureError)?;

    // NULL character becomes size 1 from size 2
    if description_len != desc.len() - 1 {
        return Err(StructureError);
    }

    offset += description_len;

    let next_dpapi_structure = vec![
        ("crypto_algorithm", "u32"),
        ("crypti_alg_len", "u32"),
        ("salt_len", "u32"),
    ];
    dpapi_header.extend(common::parse(
        &dpapi_blob_data[offset..],
        &next_dpapi_structure,
        "little",
    )?);
    let salt_len = dpapi_header["salt_len"];
    offset += (32 + 32 + 32) / 8 + salt_len;

    let next_dpapi_structure = vec![("hmac_key_len", "u32")];
    dpapi_header.extend(common::parse(
        &dpapi_blob_data[offset..],
        &next_dpapi_structure,
        "little",
    )?);
    let hmac_key_len = dpapi_header["hmac_key_len"];
    offset += 32 / 8 + hmac_key_len;

    let next_dpapi_structure = vec![
        ("hash_algorithm", "u32"),
        ("hash_alg_len", "u32"),
        ("hmac2_key_len", "u32"),
    ];
    dpapi_header.extend(common::parse(
        &dpapi_blob_data[offset..],
        &next_dpapi_structure,
        "little",
    )?);
    let hmac2_key_len = dpapi_header["hmac2_key_len"];
    offset += (32 + 32 + 32) / 8 + hmac2_key_len;

    let next_dpapi_structure = vec![("data_len", "u32")];
    dpapi_header.extend(common::parse(
        &dpapi_blob_data[offset..],
        &next_dpapi_structure,
        "little",
    )?);
    let data_len = dpapi_header["data_len"];
    offset += 32 / 8 + data_len;

    let next_dpapi_structure = vec![("sign_len", "u32")];
    dpapi_header.extend(common::parse(
        &dpapi_blob_data[offset..],
        &next_dpapi_structure,
        "little",
    )?);
    let sign_len = dpapi_header["sign_len"];
    offset += 32 / 8 + sign_len;

    Ok(DPAPIBlobHeader {
        header_size: (32 * 13 + 128 * 2) / 8,
        blob_size: offset,
        version: dpapi_header["version"],
        provider_id: dpapi_header["provider_id"],
        master_key_version: dpapi_header["master_key_version"],
        master_key_id: dpapi_header["master_key_id"],
        flags: dpapi_header["flags"],
        description_len,
        crypto_algorithm: dpapi_header["crypto_algorithm"],
        crypti_alg_len: dpapi_header["crypti_alg_len"],
        salt_len,
        hmac_key_len,
        hash_algorithm: dpapi_header["hash_algorithm"],
        hash_alg_len: dpapi_header["hash_alg_len"],
        hmac2_key_len,
        data_len,
        sign_len,
    })
}

/// Convert &[u8] into &[u16] as vec
fn utf8_to_utf16(byte_array: &[u8]) -> Option<Vec<u16>> {
    let mut utf16_vec = Vec::with_capacity(byte_array.len() / 2);
    for i in 0..utf16_vec.len() {
        let buff = byte_array[2 * i..=2 * i + 1].try_into().ok()?;
        utf16_vec[i] = u16::from_be_bytes(buff); // Big endian as to keep bit order
    }
    Some(utf16_vec)
}
