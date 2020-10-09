import os
import tempfile
import unittest

from maflib.tests.testutils import GdcV1_0_0_PublicScheme
from maflib.tests.testutils import TestCase
from maflib.tests.testutils import read_lines
from maflib.tests.testutils import tmp_file
from maflib.util import captured_output
from maftools.__main__ import main
from maftools.tests import TestMaf
from maftools.tests.utils import run_main
from maflib.header import MafHeader
from maflib.record import MafRecord
from maflib.scheme_factory import find_scheme
from maflib.sort_order import BarcodesAndCoordinate

class TestSort(TestCase):
    def read_test_maf(self):
        lines = read_lines(TestMaf)
        state = 0
        header = []
        records = []
        for line in lines:
            if line.startswith(MafHeader.HeaderLineStartSymbol):
                header.append(line)
            elif state == 0:
                state = 1
                header.append(line)
            else:
                records.append(line)
        return lines, header, records

    def __sort(self, lines, extra_args, test_func, to_stdout=False):
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

    def test_no_inputs(self):
        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit) as context:
                main(args=['sort'])

    def test_with_fasta_index(self):
        # change the order of chromosomes!
        fasta_index_lines = [
            "chr13\t114364328\t2106716512\t70\t71",
            "chr1\t248956422\t112\t70\t71"
        ]
        fd, fn = tmp_file(lines=fasta_index_lines)
        lines, header, records = self.read_test_maf()
        subcommand_args = ["--version", GdcV1_0_0_PublicScheme.version(),
                           "--annotation", GdcV1_0_0_PublicScheme.annotation_spec()]
        out_lines, stdout, stderr = run_main(subcommand="sort",
                                              lines=lines,
                                              subcommand_args=subcommand_args)

        # Check that we have the same # of records
        out_records = [line for line in out_lines \
                       if not line.startswith("#") and not line.startswith("Hugo_Symbol")]
        self.assertEqual(len(out_records), len(records))

        # Check that we added the sort pragma
        sortOrderLine = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.SortOrderKey,
            BarcodesAndCoordinate.name()
        )
        self.assertTrue(sortOrderLine in out_lines)

        scheme = find_scheme(version=GdcV1_0_0_PublicScheme.version(),
                             annotation=GdcV1_0_0_PublicScheme.annotation_spec())
        # we should see chr13 before chr1
        self.assertEqual(len(out_lines)-1, len(lines)) # added the pragma
        found_chr1 = False
        for line in out_lines:
            if line.startswith(MafHeader.HeaderLineStartSymbol):
                continue
            record = MafRecord.from_line(
                line=line,
                scheme=scheme
            )
            self.assertFalse(record["Chromosome"] == "chr13" and found_chr1)
            found_chr1 = record["Chromosome"] == "chr1"
        fd.close()
        os.remove(fn)

    def test_end_to_end(self):
        lines, header, records = self.read_test_maf()

        # reverse the lines
        input_lines = header + list(reversed(records))
        subcommand_args = ["--version", GdcV1_0_0_PublicScheme.version(),
                           "--annotation", GdcV1_0_0_PublicScheme.annotation_spec()]
        out_lines, stdout, stderr = run_main(subcommand="sort",
                                              lines=input_lines,
                                              subcommand_args=subcommand_args)
        out_records = [line for line in out_lines if not line.startswith("#")]

        # Check that we have the same # of records
        out_records = [line for line in out_lines \
                       if not line.startswith("#") and not line.startswith("Hugo_Symbol")]
        self.assertEqual(len(out_records), len(records))

        # Check that we added the sort pragma
        sortOrderLine = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.SortOrderKey,
            BarcodesAndCoordinate.name()
        )
        self.assertTrue(sortOrderLine in out_lines)

        self.assertEqual(len(out_lines)-1, len(lines)) # added the pragma

if __name__ == '__main__':
    unittest.main()
