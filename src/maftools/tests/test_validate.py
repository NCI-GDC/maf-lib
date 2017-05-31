import os
import tempfile
import unittest

from maflib.header import *
from maflib.tests.testutils import GdcV1_0_0_BasicScheme, \
    GdcV1_0_0_PublicScheme, GdcV1_0_0_ProtectedScheme
from maflib.tests.testutils import TestCase
from maflib.tests.testutils import tmp_file
from maflib.util import captured_output
from maflib.validation import MafValidationErrorType
from maftools.__main__ import main


class TestValidate(TestCase):

    def __validate__(self, lines, extra_args, test_func, to_stdout=False):
        in_fh, in_fn = tmp_file(lines=lines)
        in_fh.close()

        out_fh, out_fn = tempfile.mkstemp()

        main_args = ["validate", "--input", str(in_fn)]
        if not to_stdout:
            main_args.extend(["--output", str(out_fn)])
        main_args.extend(extra_args)

        with captured_output() as (stdout, stderr):
            main(args=main_args)

        fh = open(out_fn, "r")
        out_lines = [line.rstrip("\r\n") for line in fh]
        fh.close()

        stdout = stdout.getvalue().rstrip('\r\n').split("\n")
        stderr = stderr.getvalue().rstrip('\r\n').split("\n")

        test_func(out_lines=out_lines, stdout=stdout, stderr=stderr)

        os.remove(in_fn)
        os.remove(out_fn)

    def test_max_errors(self):
        # Silly user
        extra_args = ["--max-errors", "0"]
        with captured_output() as (stdout, stderr):
            with self.assertRaises(SystemExit) as context:
                self.__validate__(lines=[], extra_args=extra_args, test_func=None)

        # Verbose Mode: there should be an error about the version missing from
        # the header!  No error about the missing column
        lines=[
            "\t".join(["c1", "c2", "c3"]),
            "\t".join(["v1", "v2", "v3"]),
            "\t".join(["v1"]),
            "\t".join(["v1", "v2"])
        ]
        extra_args = ["--max-errors", "1"]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn(["No version line found in the header"], out_lines)
            self.assertListEqual(stdout, [''])
            self.assertEqual(len(stderr), 2)
            self.assertTrue("Maximum number of errors encountered" in stderr[1])
        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

        # Verbose Mode: there should be an error in the header and records
        extra_args = ["--max-errors", "3", "--mode", "Verbose"]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn([
                "No version line found in the header",
                "No annotation.spec line found in the header",
                "On line number 3: Found '1' columns but expected '3'"],
                out_lines)
            self.assertListEqual(stdout, [''])
            self.assertTrue("Maximum number of errors encountered" in stderr[1])
        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

        # Summary Mode: there should be an error in the header and records
        extra_args = ["--max-errors", "3", "--mode", "Summary"]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn(
                ['Error Type\tCount\tDescription',
                 'HEADER_MISSING_ANNOTATION_SPEC\t1\tThe header has no annotation spec',
                 'HEADER_MISSING_VERSION\t1\tThe header has no version',
                 'RECORD_MISMATCH_NUMBER_OF_COLUMNS\t1\tThe record has an '
                 'unexpected number of columns'],
                out_lines)
            self.assertListEqual(stdout, [''])
            self.assertTrue("Maximum number of errors encountered" in stderr[1])
        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)


    def test_no_inputs(self):
        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit) as context:
                main(args=['validate'])

    def test_unknown_scheme(self):
        scheme = "not-a-scheme"
        with self.assertRaises(SystemExit):
            with captured_output():
                main(args=['validate', '--input', '/path/to/nowhere', '--version', scheme])

    def test_modes(self):
        lines=[
            "\t".join(["c1", "c2", "c3"]),
            "\t".join(["v1", "v2", "v3"]),
            "\t".join(["v4"]),
            "\t".join(["v5", "v6"])
        ]

        # Verbose
        extra_args = ["--mode", "Verbose"]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn([
                "No version line found in the header",
                "No annotation.spec line found in the header",
                "On line number 3: Found '1' columns but expected '3'",
                "On line number 4: Found '2' columns but expected '3'"],
                out_lines)
            self.assertListEqual(stdout, [''])
            self.assertEqual(len(stderr), 2)
        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

        # Summary
        extra_args = ["--mode", "Summary"]
        def test_func(out_lines, stdout, stderr):
            def to_line(error, count):
                return "\t".join(str(s) for s in [error.name, count, error.value])
            self.assertListEqual( [
                "Error Type\tCount\tDescription",
                to_line(MafValidationErrorType.HEADER_MISSING_ANNOTATION_SPEC, 1),
                to_line(MafValidationErrorType.HEADER_MISSING_VERSION, 1),
                to_line(MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS, 2)],
                out_lines)
            self.assertListEqual(stdout, [''])
            self.assertEqual(len(stderr), 2)

        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

    def test_with_scheme(self):
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, GdcV1_0_0_BasicScheme.version())]
        extra_args = ["--version", GdcV1_0_0_BasicScheme.version()]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn(["On line number 2: Found no column names"], out_lines)
            self.assertListEqual(stdout, [''])
            self.assertEqual(len(stderr), 3)
        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

    def test_to_stdout(self):
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, GdcV1_0_0_BasicScheme.version())]
        extra_args = ["--version", GdcV1_0_0_BasicScheme.version()]
        def test_func(out_lines, stdout, stderr):
            self.assertListEqualAndIn([], out_lines)
            self.assertListEqualAndIn(["On line number 2: Found no column names"], stdout)
            self.assertEqual(len(stderr), 3)

        self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func, to_stdout=True)

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
            extra_args = ["--version", scheme.version(), "--annotation", scheme.annotation_spec()]
            def test_func(out_lines, stdout, stderr):
                self.assertListEqualAndIn(["No errors found"], out_lines)
                self.assertListEqual(stdout, [''])
                self.assertEqual(len(stderr), 2)

            self.__validate__(lines=lines, extra_args=extra_args, test_func=test_func)

if __name__ == '__main__':
    unittest.main()
