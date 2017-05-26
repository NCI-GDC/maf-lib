import unittest

from maflib.tests.testutils import GdcV1_0_0_PublicScheme
from maflib.tests.testutils import TestCase
from maflib.tests.testutils import read_lines
from maflib.util import captured_output
from maftools.__main__ import main
from maftools.tests import TestMaf
from maftools.tests.testutils import test_main


class TestView(TestCase):

    def test_no_inputs(self):
        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit) as context:
                main(args=['sort'])

    def test_end_to_end(self):
        lines = read_lines(TestMaf)
        subcommand_args = ["--version", GdcV1_0_0_PublicScheme.version(),
                           "--annotation", GdcV1_0_0_PublicScheme.annotation_spec()]
        out_lines, stdout, stderr = test_main(subcommand="view",
                                              lines=lines,
                                              subcommand_args=subcommand_args)
        self.assertListEqual(out_lines, lines)


if __name__ == '__main__':
    unittest.main()
