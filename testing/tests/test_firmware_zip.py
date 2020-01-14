
import os
import binwalk

def test_firmware_zip():
    '''
    Test: Open firmware.zip, scan for signatures
    verify that all (and only) expected signatures are detected
    '''
    expected_results = [
        [0, 'Zip archive data, at least v1.0 to extract, name: dir655_revB_FW_203NA/'],
        [51, 'Zip archive data, at least v2.0 to extract, compressed size: 6395868, uncompressed size: 6422554, name: dir655_revB_FW_203NA/DIR655B1_FW203NAB02.bin'],
        [6395993, 'Zip archive data, at least v2.0 to extract, compressed size: 14243, uncompressed size: 61440, name: dir655_revB_FW_203NA/dir655_revB_release_notes_203NA.doc'],
        [6410581, 'End of Zip archive, footer length: 22'],
    ]

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.zip")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    assert len(scan_result) == 1

    # Test number of results for that module
    assert len(scan_result[0].results) == len(expected_results)

    # Test result-description
    for result, (expected_offset, expected_description) in zip(scan_result[0].results, expected_results):
        assert result.offset == expected_offset
        assert result.description == expected_description
