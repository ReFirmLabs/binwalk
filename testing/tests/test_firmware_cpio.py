
import os
import binwalk
from nose.tools import eq_, ok_

def test_firmware_cpio():
    '''
    Test: Open firmware.cpio, scan for signatures.
    Verify that at least one CPIO signature is detected.
    Verify that only CPIO signatures are detected.
    '''
    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.cpio")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # Make sure we got some results
    ok_(len(scan_result[0].results) > 0)

    # First result should be at offset 0
    eq_(scan_result[0].results[0].offset, 0)

    # Make sure the only thing found were cpio archive entries
    for result in scan_result[0].results:
        ok_(result.description.startswith("ASCII cpio archive"))
