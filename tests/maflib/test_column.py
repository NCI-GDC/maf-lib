#!/usr/bin/env python3

import unittest
from collections import OrderedDict

from maflib.column import MafColumnRecord, MafCustomColumnRecord
from maflib.column_types import FloatColumn, StringColumn
from maflib.schemes import MafScheme
from maflib.validation import MafValidationErrorType


class _TestScheme(MafScheme):
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


class TestMafColumnRecord(unittest.TestCase):
    class NullableColumn(MafColumnRecord):
        @classmethod
        def __nullable_dict__(cls):
            return {"-10": None}

    class InvalidNullableColumn(MafColumnRecord):
        @classmethod
        def __nullable_dict__(cls):
            return {10: None}

    class NoneColumn(MafColumnRecord):
        @classmethod
        def __nullable_dict__(cls):
            return None

    def test_basic_column(self):
        column = MafColumnRecord.build(
            name="key", value="value", column_index=0, description="Foo Bar"
        )
        self.assertFalse(column.is_nullable())
        self.assertIsNone(column.__nullable_values__())
        self.assertIsNone(column.__nullable_dict__())
        self.assertIsNone(column.__nullable_keys__())
        self.assertFalse(column.is_null())
        self.assertEqual(str(column), "value")

    def test_nullable_column(self):
        column = TestMafColumnRecord.NullableColumn(
            key="key", value=10, column_index=0, description="Foo Bar"
        )
        self.assertTrue(column.is_nullable())
        self.assertListEqual(column.__nullable_values__(), [None])
        self.assertDictEqual(column.__nullable_dict__(), {"-10": None})
        self.assertListEqual(column.__nullable_keys__(), ["-10"])
        self.assertFalse(column.is_null())
        self.assertEqual(str(column), "10")

    def test_invalid_nullable_column(self):
        with self.assertRaises(ValueError):
            TestMafColumnRecord.InvalidNullableColumn(
                key="key", value=10, column_index=0, description="Foo Bar"
            )

    def test_str(self):
        column = TestMafColumnRecord.NullableColumn(
            key="key", value=None, column_index=0, description="Foo Bar"
        )
        self.assertTrue(column.is_null())
        self.assertEqual(str(column), "-10")

        column = TestMafColumnRecord.NoneColumn(
            key="key", value=None, column_index=0, description="Foo Bar"
        )
        self.assertFalse(column.is_null())
        self.assertEqual(str(column), "None")

    def test_build_with_scheme(self):
        scheme = _TestScheme()

        # column found in the scheme, column index inferred
        column = MafColumnRecord.build(
            name="float", value=2.1, description="Foo Bar", scheme=scheme
        )
        self.assertEqual(str(column), "2.1")
        self.assertEqual(column.column_index, 1)

        # column found in the scheme, column index validated
        column = MafColumnRecord.build(
            name="float",
            value=2.1,
            column_index=1,
            description="Foo Bar",
            scheme=scheme,
        )
        self.assertEqual(str(column), "2.1")
        self.assertEqual(column.column_index, 1)

        # error: name not found in scheme
        with self.assertRaises(KeyError):
            MafColumnRecord.build(
                name="not-a-key",
                value=2.1,
                column_index=0,
                description="Foo Bar",
                scheme=scheme,
            )

        # error: mismatching column index
        with self.assertRaises(ValueError):
            MafColumnRecord.build(
                name="float",
                value=2.1,
                column_index=0,
                description="Foo Bar",
                scheme=scheme,
            )


class TestMafCustomColumnRecord(unittest.TestCase):
    class ValidColumn(MafCustomColumnRecord):
        @classmethod
        def __build__(cls, value):
            return value

        def __validate__(self):
            return None

    class InvalidColumn(MafCustomColumnRecord):
        @classmethod
        def __build__(cls, value):
            return value

        def __validate__(self):
            return "invalid"

    class NullableColumn(MafCustomColumnRecord):
        @classmethod
        def __nullable_dict__(cls):
            return {"-10": None}

    def test_validate(self):
        valid = TestMafCustomColumnRecord.ValidColumn.build("key", "value", 0)
        self.assertEqual(valid.__validate__(), None)
        self.assertEqual(len(valid.validate()), 0)

        invalid = TestMafCustomColumnRecord.InvalidColumn.build("key", "value", 0)
        self.assertEqual(invalid.__validate__(), "invalid")
        errors = invalid.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid", errors[0].message)

    def test_validate_with_scheme(self):
        scheme = _TestScheme()

        # FAIL: the column has the wrong name
        column = TestMafCustomColumnRecord.ValidColumn.build("noop", "value", 0)
        errors = column.validate(scheme=scheme)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].tpe, MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES
        )
        # OK: no scheme
        self.assertEqual(len(column.validate(scheme=None)), 0)

        # OK: the lack of a column index is fine
        column = StringColumn.build("str1", "value")
        errors = column.validate(scheme=scheme)
        self.assertEqual(len(errors), 0)

        # FAIL: wrong column index
        column = StringColumn.build("str1", "value", 1)
        errors = column.validate(scheme=scheme)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].tpe, MafValidationErrorType.RECORD_COLUMN_OUT_OF_ORDER
        )
        # OK: no scheme
        self.assertEqual(len(column.validate(scheme=None)), 0)

        # FAIL: the type of the column is wrong
        column = StringColumn.build("float", "value")
        errors = column.validate(scheme=scheme)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].tpe, MafValidationErrorType.RECORD_COLUMN_WRONG_FORMAT
        )
        # OK: no scheme
        self.assertEqual(len(column.validate(scheme=None)), 0)

    def test_build_with_scheme(self):
        scheme = _TestScheme()

        # column found in the scheme, column index inferred
        column = MafCustomColumnRecord.build(
            name="float", value=2.1, description="Foo Bar", scheme=scheme
        )
        self.assertEqual(str(column), "2.1")
        self.assertEqual(column.column_index, 1)

    def test_build_nullable(self):
        column = TestMafCustomColumnRecord.NullableColumn.build_nullable(name="Name")
        self.assertIsNone(column.value)
        self.assertEqual(str(column), "-10")

        with self.assertRaises(ValueError):
            TestMafCustomColumnRecord.ValidColumn.build_nullable(name="Name")


# __END__
