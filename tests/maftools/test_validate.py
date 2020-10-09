import unittest

from maflib.header import *
from maflib.tests.testutils import GdcV1_0_0_BasicScheme, \
    GdcV1_0_0_PublicScheme, GdcV1_0_0_ProtectedScheme
from maflib.tests.testutils import TestCase
from maflib.tests.testutils import read_lines
from maflib.util import captured_output
from maflib.validation import MafValidationErrorType
from maftools.__main__ import main
from maftools.tests import TestMaf
from maftools.tests.utils import run_main


class TestValidate(TestCase):

    def __validate__(self,
                     lines,
                     subcommand_args=None,
                     to_stdout=False):
        return run_main(subcommand="validate",
                         lines=lines,
                         subcommand_args=subcommand_args,
                         to_stdout=to_stdout)

    def test_max_errors(self):
        # Silly user
        subcommand_args = ["--max-errors", "0"]
        with captured_output() as (stdout, stderr):
            with self.assertRaises(SystemExit) as context:
                self.__validate__(lines=[], subcommand_args=subcommand_args)

        # Verbose Mode: there should be an error about the version missing from
        # the header!  No error about the missing column
        lines=[
            "\t".join(["c1", "c2", "c3"]),
            "\t".join(["v1", "v2", "v3"]),
            "\t".join(["v1"]),
            "\t".join(["v1", "v2"])
        ]
        subcommand_args = ["--max-errors", "1"]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqual(stdout, [''])
        self.assertEqual(len(stderr), 2)
        self.assertTrue("Maximum number of errors encountered" in stderr[1])

        # Verbose Mode: there should be an error in the header and records
        subcommand_args = ["--max-errors", "3", "--mode", "Verbose"]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqualAndIn([
            "No version line found in the header",
            "No annotation.spec line found in the header",
            "On line number 3: Found '1' columns but expected '3'"],
            out_lines)
        self.assertListEqual(stdout, [''])
        self.assertTrue("Maximum number of errors encountered" in stderr[1])

        # Summary Mode: there should be an error in the header and records
        subcommand_args = ["--max-errors", "3", "--mode", "Summary"]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqualAndIn(
            ['Error Type\tCount\tDescription',
             'HEADER_MISSING_ANNOTATION_SPEC\t1\tThe header has no annotation spec',
             'HEADER_MISSING_VERSION\t1\tThe header has no version',
             'RECORD_MISMATCH_NUMBER_OF_COLUMNS\t1\tThe record has an '
             'unexpected number of columns'],
            out_lines)
        self.assertListEqual(stdout, [''])
        self.assertTrue("Maximum number of errors encountered" in stderr[1])

    def test_no_inputs(self):
        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit) as context:
                main(args=['validate'])

    def test_modes(self):
        lines=[
            "\t".join(["c1", "c2", "c3"]),
            "\t".join(["v1", "v2", "v3"]),
            "\t".join(["v4"]),
            "\t".join(["v5", "v6"])
        ]

        # Verbose
        subcommand_args = ["--mode", "Verbose"]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqualAndIn([
            "No version line found in the header",
            "No annotation.spec line found in the header",
            "On line number 3: Found '1' columns but expected '3'",
            "On line number 4: Found '2' columns but expected '3'"],
            out_lines)
        self.assertListEqual(stdout, [''])
        self.assertEqual(len(stderr), 2)

        # Summary
        subcommand_args = ["--mode", "Summary"]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)

        def to_line(error, count):
            return "\t".join(str(s) for s in [error.name, count, error.value])

        self.assertListEqual([
            "Error Type\tCount\tDescription",
            to_line(MafValidationErrorType.HEADER_MISSING_ANNOTATION_SPEC, 1),
            to_line(MafValidationErrorType.HEADER_MISSING_VERSION, 1),
            to_line(MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS,
                    2)],
            out_lines)
        self.assertListEqual(stdout, [''])
        self.assertEqual(len(stderr), 2)

    def test_with_scheme(self):
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, GdcV1_0_0_BasicScheme.version())]
        subcommand_args = ["--version", GdcV1_0_0_BasicScheme.version()]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqualAndIn(["On line number 2: Found no column names"],
                                  out_lines)
        self.assertListEqual(stdout, [''])
        self.assertEqual(len(stderr), 3)

    def test_to_stdout(self):
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, GdcV1_0_0_BasicScheme.version())]
        subcommand_args = ["--version", GdcV1_0_0_BasicScheme.version()]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args,
            to_stdout=True)
        self.assertListEqualAndIn([], out_lines)
        self.assertListEqualAndIn(["On line number 2: Found no column names"],
                                  stdout)
        self.assertEqual(len(stderr), 3)

    def test_no_errors(self):
        for scheme in [GdcV1_0_0_BasicScheme(), GdcV1_0_0_PublicScheme(), GdcV1_0_0_ProtectedScheme()]:
            if scheme.is_basic():
                lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, scheme.version()),
                         "\t".join(scheme.column_names())
                         ]
            else:
                lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, scheme.version()),
                         "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.AnnotationSpecKey, scheme.annotation_spec()),
                         "\t".join(scheme.column_names())
                         ]
            subcommand_args = ["--version", scheme.version(), "--annotation", scheme.annotation_spec()]
            out_lines, stdout, stderr = self.__validate__(
                lines=lines,
                subcommand_args=subcommand_args)
            self.assertListEqualAndIn(["No errors found"], out_lines)
            self.assertListEqual(stdout, [''])
            self.assertEqual(len(stderr), 2)

    def test_end_to_end(self):
        lines = read_lines(TestMaf)
        subcommand_args = ["--version", GdcV1_0_0_PublicScheme.version(),
                           "--annotation", GdcV1_0_0_PublicScheme.annotation_spec()]
        out_lines, stdout, stderr = self.__validate__(
            lines=lines,
            subcommand_args=subcommand_args)
        self.assertListEqualAndIn(["No errors found"], out_lines)
        self.assertListEqual(stdout, [''])
        self.assertEqual(len(stderr), 2)

if __name__ == '__main__':
    unittest.main()
