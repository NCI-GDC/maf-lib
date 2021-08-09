import unittest
from collections import OrderedDict

from maflib.column_types import FloatColumn, StringColumn
from maflib.record import MafColumnRecord, MafRecord
from maflib.schemes import MafScheme
from maflib.validation import MafValidationErrorType, ValidationStringency


class TestMafRecord(unittest.TestCase):
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

    def test_empty_record(self):
        record = MafRecord()
        record.validate()
        self.assertTrue(len(record.validation_errors) == 0)

    # test some basic operations
    def test_basic_operations(self):
        record = MafRecord()

        # try and get a record that's not there
        with self.assertRaises(KeyError):
            column = record["hello"]
        with self.assertRaises(KeyError):
            column = record[1]
        self.assertEqual(len(record.validate()), 0)
        self.assertIsNone(record.value("key"))

        # add a column should be OK
        column = MafColumnRecord("key", "value")
        record["key"] = column
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(column.column_index, 0)

        # get the number of columns
        self.assertEqual(len(record), 1)

        # get the column by name and column index
        self.assertEqual(record["key"], column)
        self.assertEqual(record[0], column)
        self.assertEqual(record["key"].value, column.value)
        self.assertEqual(record.value("key"), column.value)

        # overwrite it
        column = MafColumnRecord("key", "value2")
        record["key"] = column
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(len(record), 1)
        self.assertEqual(record["key"], column)
        self.assertEqual(record["key"].value, column.value)
        self.assertEqual(record.value("key"), column.value)
        self.assertEqual(column.column_index, 0)

        # add a second column
        column2 = MafColumnRecord("key2", "value3")
        record["key2"] = column2
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(len(record), 2)
        self.assertEqual(record["key"], column)
        self.assertEqual(record["key2"], column2)
        self.assertEqual(column2.column_index, 1)

        # delete the first column by name, which sets the value to None
        del record["key"]
        validation_errors = record.validate()
        self.assertEqual(len(validation_errors), 1)
        self.assertEqual(
            validation_errors[0].tpe, MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE
        )
        self.assertEqual(
            len(record), 2
        )  # NB: the first column is None, the second is `column2`
        self.assertEqual(record["key2"], column2)
        self.assertIsNone(record[0])
        with self.assertRaises(KeyError):
            column = record["key"]

        # delete the second column by index, which should make the record empty
        del record["key2"]
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(len(record), 0)

    def test_access_with_different_types(self):
        record = MafRecord()
        column = MafColumnRecord(key="key1", value="value2", column_index=0)

        # via int
        record[column.column_index] = column
        self.assertIn(column.column_index, record)
        self.assertEqual(record[column.column_index], column)
        del record[column.column_index]
        self.assertEqual(len(record), 0)
        self.assertFalse(column.column_index in record)

        # via MafColumnRecord
        record[column] = column
        self.assertIn(column, record)
        self.assertEqual(record[column], column)
        del record[column]
        self.assertEqual(len(record), 0)
        self.assertFalse(column in record)

        # via str
        record[column.key] = column
        self.assertIn(column.key, record)
        self.assertEqual(record[column.key], column)
        del record[column.key]
        self.assertEqual(len(record), 0)
        self.assertFalse(column.key in record)

    def test_setitem_in_order_and_delitem_in_reverse(self):
        record = MafRecord()

        # add the columns in order
        for i in range(0, 10):
            record["key%d" % i] = MafColumnRecord("key%d" % i, "value%d" % i)
        self.assertEqual(len(record), 10)
        self.assertEqual(len(record.validate()), 0)
        self.assertListEqual(list(record.keys()), ["key%d" % i for i in range(0, 10)])
        self.assertListEqual(
            [column.value for column in record.values()],
            ["value%d" % i for i in range(0, 10)],
        )

        # delete in the reverse order
        keys = list(record.keys())
        for i in range(9, -1, -1):
            column = record[i]
            self.assertIn(column, record)
            if i % 2 == 0:
                del record[i]
            else:
                del record[keys[i]]
            self.assertFalse(column in record)
            self.assertEqual(len(record), i)
            self.assertEqual(len(record.validate()), 0)
            self.assertListEqual(
                list(record.keys()), ["key%d" % j for j in range(0, i)]
            )
            self.assertListEqual(
                [column.value for column in record.values()],
                ["value%d" % j for j in range(0, i)],
            )

    def test_setitem_and_delitem_every_other(self):
        record = MafRecord()

        # add every other
        for i in range(0, 10, 2):
            record["key%d" % i] = MafColumnRecord(
                "key%d" % i, "value%d" % i, column_index=i
            )
        self.assertEqual(len(record), 9)
        validation_errors = record.validate()
        self.assertEqual(len(validation_errors), 4)
        self.assertListEqual(
            [error.tpe for error in validation_errors],
            [MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE]
            * 4,  # records 1, 3, 5, 7
        )
        self.assertListEqual(
            list(record.keys()),
            ["key%d" % i if (i % 2 == 0) else None for i in range(0, 9)],
        )
        self.assertListEqual(
            record.column_values(),
            ["value%d" % i if (i % 2 == 0) else None for i in range(0, 9)],
        )

    def test_getitem_with_column_index_out_of_range(self):
        record = MafRecord()
        with self.assertRaises(KeyError):
            column = record[0]
        record[0] = MafColumnRecord(key="key1", value="value2")
        with self.assertRaises(KeyError):
            column = record[-1]
        with self.assertRaises(KeyError):
            column = record[2]

    def test_getitem_with_missing_key(self):
        record = MafRecord()
        with self.assertRaises(KeyError):
            column = record[0]
        with self.assertRaises(KeyError):
            column = record[MafColumnRecord(key="key1", value="value2")]
        with self.assertRaises(KeyError):
            column = record["key"]

    def test_getitem_with_wrong_type(self):
        record = MafRecord()
        with self.assertRaises(TypeError):
            column = record[list()]

    def test_getitem_with_none_key(self):
        record = MafRecord()
        self.assertIsNone(record[None])

    def test_setitem_with_wrong_type(self):
        record = MafRecord()
        with self.assertRaises(TypeError):
            record[42.42] = MafColumnRecord("key", "value")
        with self.assertRaises(TypeError):
            record["key2"] = 42.42
        with self.assertRaises(TypeError):
            record[None] = MafColumnRecord("key", "value")

    def test_setitem_with_mismatching_name_and_column_name(self):
        record = MafRecord()
        with self.assertRaises(ValueError):
            record["key2"] = MafColumnRecord("key1", "value1")

    def test_setitem_negative_column_index(self):
        record = MafRecord()
        with self.assertRaises(KeyError):
            record[-1] = MafColumnRecord("key1", "value1")

    def test_setitem_mismatching_column_index(self):
        record = MafRecord()
        with self.assertRaises(ValueError):
            record[0] = MafColumnRecord("key1", "value1", column_index=1)

    def test_setitem_mismatching_column_keys(self):
        record = MafRecord()
        with self.assertRaises(ValueError):
            column_old = MafColumnRecord("key1", "value1", column_index=1)
            column_new = MafColumnRecord("key2", "value2", column_index=2)
            record[column_old] = column_new

    def test_setitem_mismatching_column_indexes(self):
        record = MafRecord()
        column_old = MafColumnRecord("key1", "value1", column_index=0)
        record[column_old.key] = column_old
        column_new = MafColumnRecord("key1", "value1", column_index=1)
        with self.assertRaises(ValueError):
            record[column_old] = column_new

    def test_delitem_none_column(self):
        record = MafRecord()
        column = MafColumnRecord("key1", "value1", column_index=1)
        record[column.key] = column
        with self.assertRaises(KeyError):
            del record[0]  # there is no column at index zero!

    def test_delitem_various_columns(self):
        # The aim is to make sure that when there are columns that have None values, they are removed when the next
        # column is removed.
        record = MafRecord()
        record[0] = MafColumnRecord("key0", "value0", column_index=0)
        record[1] = MafColumnRecord("key1", "value1", column_index=1)
        record[4] = MafColumnRecord("key4", "value4", column_index=4)
        record.validate()
        self.assertEqual(len(record), 5)
        self.assertEqual(len(record.validation_errors), 2)  # two missing columns: 2 & 3
        types = list(set([error.tpe for error in record.validation_errors]))
        self.assertEqual(len(types), 1)  # only one error
        self.assertEqual(types[0], MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE)

        del record[1]
        record.validate()
        self.assertEqual(len(record), 5)
        self.assertEqual(
            len(record.validation_errors), 3
        )  # three missing columns: 1, 2, & 3
        types = list(set([error.tpe for error in record.validation_errors]))
        self.assertEqual(len(types), 1)  # only one error
        self.assertEqual(types[0], MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE)

        del record[4]
        record.validate()
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record.validation_errors), 0)  # all good

        del record[0]
        record.validate()
        self.assertEqual(len(record), 0)
        self.assertEqual(len(record.validation_errors), 0)  # all good

    def test_add(self):
        record = MafRecord()
        column = MafColumnRecord("key1", "value1", column_index=0)
        self.assertEqual(record.add(column), record)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(record[0], column)

    def test_iadd(self):
        record = MafRecord()
        column = MafColumnRecord("key1", "value1", column_index=0)
        previous_record = record
        record += column
        self.assertEqual(record, previous_record)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(record[0], column)

    def test_str(self):
        record = MafRecord()
        record.add(MafColumnRecord("key1", "value1"))
        record.add(MafColumnRecord("key2", "value2"))
        self.assertEqual(len(record.validate()), 0)
        self.assertEqual(
            str(record), MafRecord.ColumnSeparator.join(["value1", "value2"])
        )

    def test_column_values(self):
        record = MafRecord()
        record.add(MafColumnRecord("key1", "value1"))
        record.add(MafColumnRecord("key2", "value2"))
        self.assertEqual(len(record.validate()), 0)
        self.assertListEqual(record.column_values(), ["value1", "value2"])

    def test_from_line_mismatch_number_of_columns(self):
        record = MafRecord.from_line(
            line=MafRecord.ColumnSeparator.join(["value1", "value2", "value3"]),
            column_names=["key1", "key2"],
            validation_stringency=ValidationStringency.Silent,
        )
        self.assertEqual(len(record), 0)
        self.assertEqual(len(record.validation_errors), 1)
        self.assertEqual(
            record.validation_errors[0].tpe,
            MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS,
        )

    def test_from_line_neither_column_names_nor_scheme(self):
        with self.assertRaises(ValueError):
            MafRecord.from_line(
                line=MafRecord.ColumnSeparator.join(["value1", "value2", "value3"]),
                validation_stringency=ValidationStringency.Silent,
            )

    def test_from_line_valid(self):
        column_names = ["key1", "key2", "key3"]
        values = ["value1", "value2", "value3"]
        record = MafRecord.from_line(
            line=MafRecord.ColumnSeparator.join(values),
            column_names=column_names,
            validation_stringency=ValidationStringency.Silent,
        )
        self.assertEqual(len(record), 3)
        self.assertEqual(len(record.validation_errors), 0)
        self.assertListEqual(list(record.keys()), column_names)
        self.assertListEqual(record.column_values(), values)

    def test_from_line_with_scheme_column_out_of_order(self):
        scheme = TestMafRecord.TestScheme()
        column_names = ["str2", "float", "str1"]
        values = ["string2", "3.14", "string1"]
        record = MafRecord.from_line(
            line=MafRecord.ColumnSeparator.join(values),
            column_names=column_names,
            scheme=scheme,
            validation_stringency=ValidationStringency.Silent,
        )
        self.assertEqual(len(record), 2)
        self.assertListEqual(record.column_values(), [None, 3.14])
        self.assertEqual(len(record.validation_errors), 3)
        self.assertListEqual(
            [e.tpe for e in record.validation_errors],
            [
                MafValidationErrorType.RECORD_COLUMN_OUT_OF_ORDER,
                MafValidationErrorType.RECORD_COLUMN_OUT_OF_ORDER,
                MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE,
            ],
        )

    def test_from_line_with_scheme_failed_to_build(self):
        scheme = TestMafRecord.TestScheme()
        values = ["string1", "string2", "string3"]
        record = MafRecord.from_line(
            line=MafRecord.ColumnSeparator.join(values),
            scheme=scheme,
            validation_stringency=ValidationStringency.Silent,
        )
        self.assertEqual(len(record), 3)
        self.assertListEqual(record.column_values(), ["string1", None, "string3"])
        self.assertEqual(len(record.validation_errors), 2)
        self.assertListEqual(
            [e.tpe for e in record.validation_errors],
            [
                MafValidationErrorType.RECORD_INVALID_COLUMN_VALUE,
                MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE,
            ],
        )

    def test_from_line_with_scheme_invalid_column_name(self):
        scheme = TestMafRecord.TestScheme()
        column_names = ["no-name", "float", "str2"]
        values = ["string1", "3.14", "string3"]
        record = MafRecord.from_line(
            line=MafRecord.ColumnSeparator.join(values),
            column_names=column_names,
            scheme=scheme,
            validation_stringency=ValidationStringency.Silent,
        )
        self.assertEqual(len(record), 3)
        self.assertListEqual(record.column_values(), [None, 3.14, "string3"])
        self.assertEqual(len(record.validation_errors), 2)
        self.assertListEqual(
            [e.tpe for e in record.validation_errors],
            [
                MafValidationErrorType.SCHEME_MISMATCHING_COLUMN_NAMES,
                MafValidationErrorType.RECORD_COLUMN_WITH_NO_VALUE,
            ],
        )

    def test_with_scheme_diff_num_columns(self):
        scheme = TestMafRecord.TestScheme()
        record = MafRecord()
        column_names = scheme.column_names()
        column_names = column_names[: len(column_names) - 1]
        column_values = ["string1", "3.14"]

        for column_index, column_name in enumerate(column_names):
            column_class = scheme.column_class(column_name)
            column = column_class.build(
                name=column_name,
                value=column_values[column_index],
                column_index=column_index,
            )
            record[column_name] = column
        record.validate(scheme=scheme)
        self.assertEqual(len(scheme.column_names()), 3)
        self.assertEqual(len(record), 2)
        self.assertEqual(len(record.validation_errors), 1)
        self.assertListEqual(
            [e.tpe for e in record.validation_errors],
            [MafValidationErrorType.RECORD_MISMATCH_NUMBER_OF_COLUMNS],
        )


# TODO: test MafRecord.from_line without column_names

if __name__ == '__main__':
    unittest.main()
