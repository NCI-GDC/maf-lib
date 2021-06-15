#!/usr/bin/env python3

import tempfile
from collections import OrderedDict

from maflib.column_types import FloatColumn, IntegerColumn, StringColumn
from maflib.header import MafHeader
from maflib.locatable import Locatable
from maflib.reader import MafReader
from maflib.record import MafRecord
from maflib.schemes.base import MafScheme
from maflib.sort_order import Coordinate
from maflib.util import captured_output
from maflib.validation import (
    MafFormatException,
    MafValidationErrorType,
    ValidationStringency,
)
from maflib.writer import MafWriter
from tests.maflib.testutils import GdcV1_0_0_ProtectedScheme, TestCase, read_lines


class TestMafWriter(TestCase):
    Scheme = GdcV1_0_0_ProtectedScheme()
    Version = Scheme.version()
    AnnotationSpec = Scheme.annotation_spec()

    __version_line = "%s%s %s" % (
        MafHeader.HeaderLineStartSymbol,
        MafHeader.VersionKey,
        Version,
    )
    __annotation_line = "%s%s %s" % (
        MafHeader.HeaderLineStartSymbol,
        MafHeader.AnnotationSpecKey,
        AnnotationSpec,
    )
    __keys_line = MafRecord.ColumnSeparator.join(Scheme.column_names())

    class TestScheme(MafScheme):
        @classmethod
        def version(cls):
            return "test-version"

        @classmethod
        def annotation_spec(cls):
            return "test-annotation"

        @classmethod
        def __column_dict__(cls):
            return OrderedDict(
                [("str1", StringColumn), ("float", FloatColumn), ("str2", StringColumn)]
            )

    def test_empty_file(self):
        fd, path = tempfile.mkstemp()

        # No logging to stderr/stdout
        with captured_output() as (stdout, stderr):
            writer = MafWriter.from_path(
                path=path,
                header=MafHeader(),
                validation_stringency=ValidationStringency.Silent,
            )
            writer.close()
            self.assertEqual(read_lines(path), [])
            self.assertEqual(str(writer.header()), "")
        stdout = stdout.getvalue().rstrip('\r\n').split("\n")
        stderr = stderr.getvalue().rstrip('\r\n').split("\n")
        self.assertListEqual(stdout, [''])
        self.assertListEqual(stderr, [''])

        # Logging to stderr/stdout
        with captured_output() as (stdout, stderr):
            writer = MafWriter.from_path(
                path=path,
                header=MafHeader(),
                validation_stringency=ValidationStringency.Lenient,
            )
            writer.close()
            self.assertEqual(read_lines(path), [])
            self.assertEqual(str(writer.header()), "")
        stdout = stdout.getvalue().rstrip('\r\n').split("\n")
        stderr = stderr.getvalue().rstrip('\r\n').split("\n")
        self.assertListEqual(stdout, [''])
        self.assertListEqualAndIn(
            ['HEADER_MISSING_VERSION', 'HEADER_MISSING_ANNOTATION_SPEC'], stderr
        )

        #  Exceptions
        with captured_output():
            with self.assertRaises(MafFormatException) as context:
                writer = MafWriter.from_path(
                    path=path,
                    header=MafHeader(),
                    validation_stringency=ValidationStringency.Strict,
                )
            self.assertEqual(
                context.exception.tpe, MafValidationErrorType.HEADER_MISSING_VERSION
            )

    def test_gz_support(self):
        fd, path = tempfile.mkstemp(suffix=".gz")

        lines = [
            TestMafWriter.__version_line,
            TestMafWriter.__annotation_line,
            "#key1 value1",
            "#key2 value2",
            TestMafWriter.__keys_line,
        ]
        with captured_output() as (stdout, stderr):
            header = MafHeader.from_lines(lines=lines)
            writer = MafWriter.from_path(header=header, path=path)
            writer.close()
            self.assertListEqual(read_lines(path), lines)
            self.assertEqual(
                str(writer.header()) + "\n" + TestMafWriter.__keys_line,
                "\n".join(lines),
            )
        stdout = stdout.getvalue().rstrip('\r\n').split("\n")
        stderr = stderr.getvalue().rstrip('\r\n').split("\n")
        self.assertListEqual(stdout, [''])
        self.assertListEqual(stderr, [''])

    def test_close(self):
        fd, path = tempfile.mkstemp()

        lines = [
            TestMafWriter.__version_line,
            TestMafWriter.__annotation_line,
            "#key1 value1",
            "#key2 value2",
            TestMafWriter.__keys_line,
        ]
        header = MafHeader.from_lines(lines=lines)
        writer = MafWriter.from_path(header=header, path=path)
        writer._handle.write("LAST")  # Naughty
        writer.close()
        self.assertListEqual(read_lines(path), lines + ["LAST"])

        with self.assertRaises(ValueError):
            writer._handle.write("Oh no")

    def add_records(self):
        scheme = TestMafWriter.TestScheme()
        fd, path = tempfile.mkstemp()

        header_lines = MafHeader.scheme_header_lines(scheme) + [
            "#key1 value1",
            "#key2 value2",
        ]
        header = MafHeader.from_lines(lines=header_lines)
        writer = MafWriter.from_path(header=header, path=path)
        values = ["string2", "3.14", "string1"]
        record_line = MafRecord.ColumnSeparator.join(values)
        record = MafRecord.from_line(line=record_line, scheme=scheme, line_number=1)
        writer += record
        writer.write(record)
        writer.close()

        self.assertListEqual(
            read_lines(path), header_lines + [record_line, record_line]
        )

    def test_record_validation_error(self):
        scheme = TestMafWriter.TestScheme()
        fd, path = tempfile.mkstemp()

        # Create the header
        header_lines = (
            MafHeader.scheme_header_lines(scheme)
            + ["#key1 value1", "#key2 value2"]
            + ["str1\tNone\tstr2"]
        )
        header = MafHeader.from_lines(
            lines=header_lines, validation_stringency=ValidationStringency.Silent
        )

        # Create the record
        values = ["string2", "error", "string1"]
        record_line = MafRecord.ColumnSeparator.join(values)
        record = MafRecord.from_line(
            line=record_line,
            scheme=scheme,
            line_number=1,
            validation_stringency=ValidationStringency.Silent,
        )

        # Write the header, and the record twice
        with captured_output() as (stdout, stderr):
            writer = MafWriter.from_path(
                header=header,
                validation_stringency=ValidationStringency.Lenient,
                path=path,
            )
            writer += record
            writer.write(record)
            writer.close()
        stdout = stdout.getvalue().rstrip('\r\n').split("\n")
        stderr = stderr.getvalue().rstrip('\r\n').split("\n")
        self.assertListEqual(stdout, [''])

        # The errors that should be written stderr
        errors = [
            "HEADER_UNSUPPORTED_VERSION",
            "HEADER_UNSUPPORTED_ANNOTATION_SPEC",
            "RECORD_COLUMN_WITH_NO_VALUE",
            "RECORD_COLUMN_WITH_NO_VALUE",
        ]
        self.assertListEqualAndIn(errors, stderr)

        # The second column should be None
        err_record_line = record_line.replace("error", "None")
        self.assertListEqual(
            read_lines(path), header_lines + [err_record_line, err_record_line]
        )

    class TestCoordinateScheme(MafScheme):
        @classmethod
        def version(cls):
            return "test-version"

        @classmethod
        def annotation_spec(cls):
            return "test-annotation"

        @classmethod
        def __column_dict__(cls):
            return OrderedDict(
                [
                    ("Chromosome", StringColumn),
                    ("Start_Position", IntegerColumn),
                    ("End_Position", IntegerColumn),
                ]
            )

    class DummyRecord(Locatable):
        def __init__(self, chr, start, end):
            self._dict = OrderedDict()
            self._dict["Chromosome"] = chr
            self._dict["Start_Position"] = start
            self._dict["End_Position"] = end
            super(TestMafWriter.DummyRecord, self).__init__(chr, start, end)

        def value(self, key):
            return self._dict[key]

        def keys(self):
            return self._dict.keys()

        def validate(self, *args, **kwargs):
            return None

        def __str__(self):
            return "\t".join([str(v) for v in self._dict.values()])

    def test_with_sorting(self):
        scheme = TestMafWriter.TestCoordinateScheme()
        fd, path = tempfile.mkstemp()

        # Create the header
        header_lines = (
            MafHeader.scheme_header_lines(scheme)
            + ["#key1 value1", "#key2 value2"]
            + [
                "%s%s %s"
                % (
                    MafHeader.HeaderLineStartSymbol,
                    MafHeader.SortOrderKey,
                    Coordinate().name(),
                )
            ]
            + ["\t".join(scheme.column_names())]
        )
        header = MafHeader.from_lines(
            lines=header_lines, validation_stringency=ValidationStringency.Silent
        )

        # Write the header, and the record twice
        writer = MafWriter.from_path(
            header=header,
            validation_stringency=ValidationStringency.Lenient,
            path=path,
            assume_sorted=False,
        )
        writer += TestMafWriter.DummyRecord("chr1", 2, 2)
        writer += TestMafWriter.DummyRecord("chr1", 3, 3)
        writer += TestMafWriter.DummyRecord("chr1", 4, 4)
        writer.close()

        reader = MafReader.reader_from(path=path, scheme=scheme)
        header = reader.header()
        records = [rec for rec in reader]
        reader.close()

        self.assertEqual(header.sort_order().name(), Coordinate.name())

        self.assertListEqual([r["Start_Position"].value for r in records], [2, 3, 4])
        self.assertListEqual([r["End_Position"].value for r in records], [2, 3, 4])


# __END__
