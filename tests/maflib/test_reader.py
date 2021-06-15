#!/usr/bin/env python3

import unittest
from collections import OrderedDict

from maflib.column_types import FloatColumn, StringColumn
from maflib.header import MafHeader
from maflib.locatable import Locatable
from maflib.reader import MafReader
from maflib.schemes.base import MafScheme
from maflib.schemes.no_restrictions_scheme import NoRestrictionsScheme
from maflib.sort_order import Coordinate
from maflib.validation import MafValidationErrorType, ValidationStringency
from tests.maflib.testutils import (
    GdcV1_0_0_BasicScheme,
    GdcV1_0_0_ProtectedScheme,
    tmp_file,
)


class TestMafReader(unittest.TestCase):
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

    class TestSchemeGdc(TestScheme):
        @classmethod
        def version(cls):
            return GdcV1_0_0_BasicScheme.version()

        @classmethod
        def annotation_spec(cls):
            return GdcV1_0_0_BasicScheme.annotation_spec()

    Scheme = TestScheme()
    Version = "%s%s %s" % (
        MafHeader.HeaderLineStartSymbol,
        MafHeader.VersionKey,
        Scheme.version(),
    )
    AnnotationSpec = "%s%s %s" % (
        MafHeader.HeaderLineStartSymbol,
        MafHeader.AnnotationSpecKey,
        Scheme.annotation_spec(),
    )
    Names = Scheme.column_names()

    def test_different_scheme_in_header(self):
        version = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            GdcV1_0_0_BasicScheme.version(),
        )
        # annotation = "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.AnnotationSpecKey, TestMafReader.Scheme.annotation_spec())
        lines = [version, "\t".join(TestMafReader.Names)]

        # When a scheme is given, we should get a HEADER_MISMATCH_SCHEME error
        reader = MafReader(lines=lines, scheme=TestMafReader.Scheme)
        self.assertIsNone(next(reader, None))
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [MafValidationErrorType.HEADER_MISMATCH_SCHEME],
        )

        # But when no scheme is given, then we should get a SCHEME_MISMATCHING_NUMBER_OF_COLUMN_NAMES error
        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [MafValidationErrorType.SCHEME_MISMATCHING_NUMBER_OF_COLUMN_NAMES],
        )

    def test_missing_column_names(self):
        lines = [TestMafReader.Version, TestMafReader.AnnotationSpec]

        # When a scheme is given, we should get get a few errors
        reader = MafReader(lines=lines, scheme=TestMafReader.Scheme)
        self.assertIsNone(next(reader, None))
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [
                MafValidationErrorType.HEADER_UNSUPPORTED_VERSION,
                MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC,
                MafValidationErrorType.HEADER_MISSING_COLUMN_NAMES,
            ],
        )

    def test_different_column_names_but_same_named_scheme(self):
        lines = [
            TestMafReader.Version,
            TestMafReader.AnnotationSpec,
            "\t".join(reversed(TestMafReader.Names)),
        ]

        # When a scheme is given, we should get get a few
        reader = MafReader(lines=lines, scheme=TestMafReader.Scheme)
        self.assertIsNone(next(reader, None))
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [
                MafValidationErrorType.HEADER_UNSUPPORTED_VERSION,
                MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC,
                MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES,
                MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES,
            ],
        )

        # But when no scheme is given, then we should not get a HEADER_MISMATCH_SCHEME error
        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [
                MafValidationErrorType.HEADER_UNSUPPORTED_VERSION,
                MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC,
            ],
        )

    def test_use_scheme_from_header_basic(self):
        version = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            GdcV1_0_0_BasicScheme.version(),
        )
        lines = [version, "\t".join(GdcV1_0_0_BasicScheme().column_names())]

        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertEqual(len(reader.validation_errors), 0)
        self.assertEqual(
            reader.header().scheme().version(), GdcV1_0_0_BasicScheme().version()
        )

    def test_use_scheme_from_header_not_basic(self):
        version = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            GdcV1_0_0_ProtectedScheme.version(),
        )
        annotation = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.AnnotationSpecKey,
            GdcV1_0_0_ProtectedScheme.annotation_spec(),
        )
        lines = [
            version,
            annotation,
            "\t".join(GdcV1_0_0_ProtectedScheme().column_names()),
        ]

        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertEqual(len(reader.validation_errors), 0)
        self.assertEqual(
            reader.header().scheme().version(), GdcV1_0_0_ProtectedScheme().version()
        )

    def test_use_default_scheme(self):
        lines = [
            TestMafReader.AnnotationSpec,
            "\t".join(GdcV1_0_0_BasicScheme().column_names()),
        ]

        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertEqual(len(reader.validation_errors), 2)
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [
                MafValidationErrorType.HEADER_MISSING_VERSION,
                MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC,
            ],
        )
        self.assertIsNone(reader.header().scheme())
        self.assertEqual(
            reader.scheme().version(),
            NoRestrictionsScheme(column_names=list()).version(),
        )

    def test_use_different_scheme(self):
        lines = [
            "%s%s %s"
            % (
                MafHeader.HeaderLineStartSymbol,
                MafHeader.VersionKey,
                GdcV1_0_0_ProtectedScheme.version(),
            ),
            "%s%s %s"
            % (
                MafHeader.HeaderLineStartSymbol,
                MafHeader.AnnotationSpecKey,
                GdcV1_0_0_ProtectedScheme.annotation_spec(),
            ),
            "\t".join(GdcV1_0_0_BasicScheme().column_names()),
        ]

        reader = MafReader(lines=lines, scheme=None)
        self.assertIsNone(next(reader, None))
        self.assertEqual(len(reader.validation_errors), 1)
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [MafValidationErrorType.SCHEME_MISMATCHING_NUMBER_OF_COLUMN_NAMES],
        )
        self.assertEqual(
            reader.header().scheme().version(), GdcV1_0_0_BasicScheme.version()
        )
        self.assertEqual(
            reader.scheme().version(), GdcV1_0_0_ProtectedScheme().version()
        )
        self.assertEqual(
            reader.scheme().annotation_spec(),
            GdcV1_0_0_ProtectedScheme.annotation_spec(),
        )
        self.assertEqual(
            reader.header().scheme().annotation_spec(),
            GdcV1_0_0_ProtectedScheme.annotation_spec(),
        )

    def test_iter(self):
        lines = [
            TestMafReader.Version,
            TestMafReader.AnnotationSpec,
            "\t".join(reversed(TestMafReader.Names)),
            "\t".join(["string1", "3.14", "string2"]),
        ]

        reader = MafReader(lines=lines, scheme=None)
        self.assertEqual(len([_ for _ in reader]), 1)

    def test_record_errors(self):
        lines = [
            TestMafReader.Version,
            TestMafReader.AnnotationSpec,
            "\t".join(TestMafReader.Names),
            "\t".join(["string1", "string-float", "string2"]),
        ]

        reader = MafReader(lines=lines, scheme=TestMafReader.Scheme)
        self.assertEqual(len([_ for _ in reader]), 1)
        self.assertListEqual(
            [e.tpe for e in reader.validation_errors],
            [
                MafValidationErrorType.HEADER_UNSUPPORTED_VERSION,
                MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC,
                MafValidationErrorType.RECORD_INVALID_COLUMN_VALUE,
                MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE,
            ],
        )

    def test_reader_from_with_scheme(self):
        scheme = TestMafReader.TestScheme()
        header = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            scheme.version(),
        )
        column_names = scheme.column_names()

        lines = [
            header,
            "\t".join(column_names),
            "\t".join(["cell-1-1", "1.314", "cell-1-2"]),
            "\t".join(["cell-2-1", "2.314", "cell-2-2"]),
            "\t".join(["cell-3-1", "3.314", "cell-3-2"]),
        ]

        fh, fn = tmp_file(lines=lines)
        fh.close()

        reader = MafReader.reader_from(
            path=fn, validation_stringency=ValidationStringency.Silent, scheme=scheme
        )
        records = [record for record in reader]

        self.assertEqual(reader.scheme().version(), scheme.version())
        self.assertEqual(reader.header().version(), scheme.version())
        self.assertEqual(len(reader.header()), 1)
        self.assertEqual(len(records), 3)
        self.assertListEqual(
            [r["str1"].value for r in records], ["cell-1-1", "cell-2-1", "cell-3-1"]
        )
        self.assertListEqual([r["float"].value for r in records], [1.314, 2.314, 3.314])

        reader.close()

    class DummyRecord(Locatable):
        def __init__(self, chr, start, end):
            self._dict = dict()
            self._dict["Chromosome"] = chr
            self._dict["Start_Position"] = start
            self._dict["End_Position"] = end
            super(TestMafReader.DummyRecord, self).__init__(chr, start, end)

        def value(self, key):
            return self._dict[key]

    def test_reader_in_order(self):
        column_names = ["Chromosome", "Start_Position", "End_Position"]
        scheme = NoRestrictionsScheme(column_names)
        header_version = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            scheme.version(),
        )
        header_sort_order = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.SortOrderKey,
            Coordinate(),
        )

        lines = [
            header_version,
            header_sort_order,
            "\t".join(column_names),
            "\t".join(["A", "1", "1"]),
            "\t".join(["A", "2", "2"]),
            "\t".join(["A", "3", "3"]),
        ]

        fh, fn = tmp_file(lines=lines)
        fh.close()

        reader = MafReader.reader_from(
            path=fn, validation_stringency=ValidationStringency.Silent, scheme=scheme
        )

        self.assertEqual(reader.scheme().version(), scheme.version())
        self.assertEqual(reader.header().version(), scheme.version())
        self.assertEqual(reader.header().sort_order().name(), Coordinate().name())

        records = [record for record in reader]
        self.assertEqual(len(records), 3)

        reader.close()

    def test_reader_out_of_order(self):
        column_names = ["Chromosome", "Start_Position", "End_Position"]
        scheme = NoRestrictionsScheme(column_names)
        header_version = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.VersionKey,
            scheme.version(),
        )
        header_sort_order = "%s%s %s" % (
            MafHeader.HeaderLineStartSymbol,
            MafHeader.SortOrderKey,
            Coordinate(),
        )

        lines = [
            header_version,
            header_sort_order,
            "\t".join(column_names),
            "\t".join(["A", "1", "1"]),
            "\t".join(["A", "4", "4"]),
            "\t".join(["A", "2", "2"]),
        ]

        fh, fn = tmp_file(lines=lines)
        fh.close()

        reader = MafReader.reader_from(
            path=fn, validation_stringency=ValidationStringency.Silent, scheme=scheme
        )

        self.assertEqual(reader.scheme().version(), scheme.version())
        self.assertEqual(reader.header().version(), scheme.version())
        self.assertEqual(reader.header().sort_order().name(), Coordinate().name())

        with self.assertRaises(ValueError):
            records = [record for record in reader]

        reader.close()


# __END__
