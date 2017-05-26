import gzip
import os
import tempfile
import unittest

from maflib.scheme_factory import find_scheme_class


def tmp_file(lines):
    """
    Creates a temporary file and writes the lines to the file.  A newline will be written after every line.  The
    temporary file should be deleted by the caller.
    :param lines: the lines to write.
    :return: the temporary file name and a file reading for reading.
    """
    (fd, fn) = tempfile.mkstemp()
    fh = os.fdopen(fd, "w")
    for line in lines:
        fh.write(line + "\n")
    fh.close()
    return [open(fn, "r"), fn]

def read_lines(path):
    if path.endswith(".gz"):
        fh = gzip.open(path, "rt")
    else:
        fh = open(path, 'r')
    lines = fh.readlines()
    fh.close()
    return [line.rstrip("\r\n") for line in lines]


class TestCase(unittest.TestCase):
    def assertListEqualAndIn(self, members, containers):
        self.assertEqual(len(members), len(containers))
        for member, container in zip(members, containers):
            self.assertIn(member, container)


GdcV1_0_0_BasicScheme = find_scheme_class(version="gdc-1.0.0",
                                          annotation="gdc-1.0.0")
GdcV1_0_0_ProtectedScheme = find_scheme_class(version="gdc-1.0.0",
                                              annotation="gdc-1.0.0-protected")
GdcV1_0_0_PublicScheme = find_scheme_class(version="gdc-1.0.0",
                                           annotation="gdc-1.0.0-public")