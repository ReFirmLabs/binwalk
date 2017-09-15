
import os
import binwalk
from nose.tools import eq_, ok_

def test_firmware_jffs2():
    '''
    Test: Open firmware.jffs2, scan for signatures.
    Verify that only JFFS2 signatures are detected.
    Verify that only the first one was displayed.
    '''
    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "firmware.jffs2")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # Test number of results for that module, should be more than one
    ok_(len(scan_result[0].results) > 1)

    first_result = scan_result[0].results[0]

    # Check the offset of the first result
    eq_(first_result.offset, 0)

    # Make sure we found the jffs file system
    ok_(first_result.description.startswith("JFFS2 filesystem"))

    # Check to make sure the first result was displayed
    ok_(first_result.display == True)

    # Make sure we only found jffs2 file system entries
    # and that nothing but the first entry was displayed
    for result in scan_result[0].results[1:]:
        ok_(result.description.startswith("JFFS2 filesystem"))
        ok_(result.display == False)

