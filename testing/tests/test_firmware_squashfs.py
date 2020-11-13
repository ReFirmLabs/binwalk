
import os
import binwalk
from nose.tools import eq_, ok_

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
    eq_(len(scan_result), 1)

    # There should be only one result
    eq_(len(scan_result[0].results), 1)

    # That result should be at offset zero
    eq_(scan_result[0].results[0].offset, 0)

    # That result should be a squashfs file system
    ok_(scan_result[0].results[0].description.startswith("Squashfs filesystem"))
