
import os
import binwalk


def test_firmware_squashfs():
    '''
    Test: Open firmware.squashfs, scan for signatures.
    Verify that one, and only one signature was detected.
    Verityf that it was a SquashFS file system.
    '''
    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.squashfs")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    assert len(scan_result) == 1

    # There should be only one result
    assert len(scan_result[0].results) == 1

    # That result should be at offset zero
    assert scan_result[0].results[0].offset == 0

    # That result should be a squashfs file system
    assert scan_result[0].results[0].description.startswith("Squashfs filesystem")
