import os
import binwalk
from nose.tools import eq_, ok_

def test_dirtraversal():
    '''
    Test: Open dirtraversal.tar, scan for signatures.
    Verify that dangerous symlinks have been sanitized.
    '''
    bad_symlink_file_list = ['foo', 'bar', 'foo2', 'bar2']
    good_symlink_file_list = ['README_link', 'README2_link']

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "dirtraversal.tar")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               extract=True,
                               quiet=True)

    # Test number of modules used
    eq_(len(scan_result), 1)

    # Make sure the bad symlinks have been sanitized and the
    # good symlinks have not been sanitized.
    for result in scan_result[0].results:
        if result.file.name in bad_symlink_file_list:
            assert_equal(os.path.realpath(result.file.path), os.devnull)
        elif result.file.name in good_symlink_file_list:
            assert_not_equal(os.path.realpath(result.file.path), os.devnull)
