import os
import binwalk
from nose.tools import eq_, ok_, assert_equal, assert_not_equal

def test_dirtraversal():
    '''
    Test: Open dirtraversal.tar, scan for signatures.
    Verify that dangerous symlinks have been sanitized.
    '''
    bad_symlink_file_list = ['foo', 'bar', 'subdir/foo2', 'subdir/bar2']
    good_symlink_file_list = ['subdir/README_link', 'README2_link']

    input_vector_file = os.path.join(os.path.dirname(__file__),
                                     "input-vectors",
                                     "dirtraversal.tar")

    output_directory = os.path.join(os.path.dirname(__file__),
                                    "input-vectors",
                                    "_dirtraversal.tar.extracted")

    scan_result = binwalk.scan(input_vector_file,
                               signature=True,
                               extract=True,
                               quiet=True)[0]

    # Make sure the bad symlinks have been sanitized and the
    # good symlinks have not been sanitized.
    for symlink in bad_symlink_file_list:
        linktarget = os.path.realpath(os.path.join(output_directory, symlink))
        assert_equal(linktarget, os.devnull)
    for symlink in good_symlink_file_list:
        linktarget = os.path.realpath(os.path.join(output_directory, symlink))
        assert_not_equal(linktarget, os.devnull)
