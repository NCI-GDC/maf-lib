# /usr/bin/env python3

import unittest
from enum import unique

from maflib import column_types, column_values
from maflib.util import extend_class


class TestCase(unittest.TestCase):
    def is_column_is_valid(self, column, value, nullable_values=None):
        if nullable_values is None:
            self.assertFalse(column.__nullable_values__())
        else:
            self.assertListEqual(column.__nullable_values__(), nullable_values)
        self.assertEqual(column.value, value)
        self.assertListEqual(column.validate(), [])
        return True

    def is_column_invalid(self, column, new_value, error_message):
        column.value = new_value
        errors = column.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn(error_message, errors[0].message)
        return True


class TestRequireNullValue(TestCase):
    def test_validate_null(self):
        base_cls = column_types.NullableDnaString
        cls = extend_class(base_cls, column_types.RequireNullValue)

        column = base_cls.build("name", "ACGT")
        self.assertEqual(len(column.validate()), 0)
        column = base_cls.build("name", "")
        self.assertEqual(len(column.validate()), 0)

        column = cls.build("name", "ACGT")
        self.assertIn("was not a null value", column.validate()[0].message)
        column = cls.build("name", "")
        self.assertEqual(len(column.validate()), 0)


class TestNullableStringColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(
            column_types.NullableStringColumn.build("key", "Foo"), "Foo", [None]
        )
        self.is_column_is_valid(
            column_types.NullableStringColumn.build("key", ""), None, [None]
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.NullableStringColumn.build("key", "Foo"),
            2,
            "'2' was not a string",
        )
        self.is_column_invalid(
            column_types.StringColumn.build("key", "Foo"),
            None,
            "'None' was not a string",
        )


class TestStringColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(column_types.StringColumn.build("key", "Foo"), "Foo")

    def test_invalid(self):
        self.is_column_invalid(
            column_types.StringColumn.build("key", "Foo"), 2, "'2' was not a string"
        )
        self.is_column_invalid(
            column_types.StringColumn.build("key", ""),
            "",
            column_types.StringColumn.EmptyStringMessage,
        )
        self.is_column_invalid(
            column_types.StringColumn.build("key", "Foo"),
            None,
            "'None' was not a string",
        )


class TestStringIntegerOrFloatColumn(TestCase):
    def test_valid(self):
        for value in ["Foo", 2, 3.14]:
            self.is_column_is_valid(
                column_types.StringIntegerOrFloatColumn.build("key", value), value
            )

    def test_invalid(self):
        column = column_types.StringIntegerOrFloatColumn.build("key", "Foo")
        self.is_column_invalid(
            column,
            None,
            column_types.StringIntegerOrFloatColumn.__type_error_message__(None),
        )

        with self.assertRaises(TypeError):
            column_types.StringIntegerOrFloatColumn.build("key", None)


class TestStringOrIntegerColumn(TestCase):
    def test_valid(self):
        for value in ["Foo", 2]:
            self.is_column_is_valid(
                column_types.StringOrIntegerColumn.build("key", value), value
            )

    def test_invalid(self):
        column = column_types.StringOrIntegerColumn.build("key", "Foo")
        self.is_column_invalid(
            column,
            None,
            column_types.StringOrIntegerColumn.__type_error_message__(None),
        )

        with self.assertRaises(TypeError):
            column_types.StringOrIntegerColumn.build("key", column)


class TestIntegerColumn(TestCase):
    class RangedIntegerColumn(column_types.IntegerColumn):
        @classmethod
        def __min_value__(cls):
            return -1

        @classmethod
        def __max_value__(cls):
            return 1

    def test_valid(self):
        self.is_column_is_valid(column_types.IntegerColumn.build("key", 1), 1)
        self.is_column_is_valid(column_types.IntegerColumn.build("key", 0), 0)

    def test_invalid(self):
        self.is_column_invalid(
            column_types.IntegerColumn.build("key", 1),
            "Foo",
            column_types.IntegerColumn.__type_error_message__("Foo"),
        )

        with self.assertRaises(ValueError):
            column_types.IntegerColumn.build("key", "")

        self.is_column_invalid(
            TestIntegerColumn.RangedIntegerColumn("key", -10), -10, "out of range (<"
        )
        self.is_column_invalid(
            TestIntegerColumn.RangedIntegerColumn("key", 10), 10, "out of range (>"
        )

    def test_zero_based(self):
        self.is_column_is_valid(column_types.ZeroBasedIntegerColumn.build("key", 0), 0)
        self.is_column_invalid(
            column_types.ZeroBasedIntegerColumn("key", -1), -1, "out of range (<"
        )

    def test_one_based(self):
        self.is_column_is_valid(column_types.OneBasedIntegerColumn.build("key", 1), 1)
        self.is_column_invalid(
            column_types.OneBasedIntegerColumn("key", 0), 0, "out of range (<"
        )


class TestNullableIntegerColumn(TestCase):
    class RangedIntegerColumn(column_types.NullableIntegerColumn):
        @classmethod
        def __min_value__(cls):
            return -1

        @classmethod
        def __max_value__(cls):
            return 1

    def test_valid(self):
        self.is_column_is_valid(
            column_types.NullableIntegerColumn.build("key", 1), 1, [None]
        )
        self.is_column_is_valid(
            column_types.NullableIntegerColumn.build("key", 0), 0, [None]
        )
        self.is_column_is_valid(
            column_types.NullableIntegerColumn.build("key", ""), None, [None]
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.NullableIntegerColumn.build("key", 1),
            "Foo",
            column_types.NullableIntegerColumn.__type_error_message__("Foo"),
        )
        self.is_column_invalid(
            TestNullableIntegerColumn.RangedIntegerColumn("key", -10),
            -10,
            "out of range (<",
        )
        self.is_column_invalid(
            TestNullableIntegerColumn.RangedIntegerColumn("key", 10),
            10,
            "out of range (>",
        )

    def test_zero_based(self):
        self.is_column_is_valid(
            column_types.NullableZeroBasedIntegerColumn.build("key", 0), 0, [None]
        )
        self.is_column_invalid(
            column_types.NullableZeroBasedIntegerColumn("key", -1),
            -1,
            "out of range (<",
        )

    def test_one_based(self):
        self.is_column_is_valid(
            column_types.NullableOneBasedIntegerColumn.build("key", 1), 1, [None]
        )
        self.is_column_invalid(
            column_types.NullableOneBasedIntegerColumn("key", 0), 0, "out of range (<"
        )


class TestFloatColumn(TestCase):
    def test_valid(self):
        for value in [1, 3.14]:
            self.is_column_is_valid(column_types.FloatColumn.build("key", value), value)

    def test_invalid(self):
        self.is_column_invalid(
            column_types.FloatColumn.build("key", 1), "Foo", "was not a float"
        )

        with self.assertRaises(ValueError):
            column_types.FloatColumn.build("key", "value")


class TestEnumColumn(TestCase):
    @unique
    class TestEnum(column_values.MafEnum):
        Foo = "1.Foo"
        Bar = "2.Bar"
        Null = "3.Null"

    class NullableEnumColumn(column_types.EnumColumn):
        @classmethod
        def __enum_class__(cls):
            return TestEnumColumn.TestEnum

        @classmethod
        def __nullable_dict__(cls):
            return {TestEnumColumn.TestEnum.Null.name: TestEnumColumn.TestEnum.Null}

    class NotNullableEnumColumn(column_types.EnumColumn):
        @classmethod
        def __enum_class__(cls):
            return TestEnumColumn.TestEnum

    def test_valid(self):
        for value in ["Foo", "1.Foo"]:
            self.is_column_is_valid(
                TestEnumColumn.NullableEnumColumn.build("key", value),
                TestEnumColumn.TestEnum.Foo,
                [TestEnumColumn.TestEnum.Null],
            )

            self.is_column_is_valid(
                TestEnumColumn.NotNullableEnumColumn.build("key", value),
                TestEnumColumn.TestEnum.Foo,
            )

    def test_invalid(self):
        with self.assertRaises(KeyError):
            TestEnumColumn.NullableEnumColumn.build("key", "NoOne")

        self.is_column_invalid(
            TestEnumColumn.NullableEnumColumn.build("key", "Foo"),
            "NoOne",
            "was not of type 'TestEnum'",
        )


class TestSequenceOfStrings(TestCase):
    def test_valid(self):
        for value in ["", "1", "1;2", "1;2;3"]:
            expected_value = value.split(";") if len(value) > 0 else []
            self.is_column_is_valid(
                column_types.SequenceOfStrings.build("key", value), expected_value, [[]]
            )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.SequenceOfStrings.build("key", "1"),
            1,
            "was neither a list nor tuple",
        )
        self.is_column_invalid(
            column_types.SequenceOfStrings.build("key", "1"), [1], "was not a string"
        )

        with self.assertRaises(ValueError):
            column_types.SequenceOfStrings.build("key", 1)

        column_types.SequenceOfStrings.build("key", "1;2;3;")


class TestSequenceOfIntegers(TestCase):
    def test_valid(self):
        input_values = ["", "1", "1;2", "1;2;3"]
        expected_values = [[], [1], [1, 2], [1, 2, 3]]
        for in_value, exp_values in zip(input_values, expected_values):
            self.is_column_is_valid(
                column_types.SequenceOfIntegers.build("key", in_value), exp_values, [[]]
            )
        self.is_column_is_valid(
            column_types.SequenceOfIntegers.build("key", ""), [], [[]]
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.SequenceOfIntegers.build("key", "1"),
            1,
            "was neither a list nor tuple",
        )
        self.is_column_invalid(
            column_types.SequenceOfIntegers.build("key", "1"),
            ["A"],
            "For the 1th value in '['A']'",
        )
        self.is_column_invalid(
            column_types.SequenceOfIntegers.build("key", "1"),
            ["1"],
            "For the 1th value in '['1']'",
        )

        with self.assertRaises(ValueError):
            column_types.SequenceOfIntegers.build("key", 1)

        with self.assertRaises(ValueError):
            column_types.SequenceOfIntegers.build("key", "1;A")

        with self.assertRaises(ValueError):
            column_types.SequenceOfIntegers.build("key", "1;A;")


class TestDnaString(TestCase):
    def test_valid(self):
        for dna in ["A", "ACGT", "GATTACA"]:
            self.is_column_is_valid(
                column_types.NullableDnaString.build("key", dna), dna, [None]
            )
            self.is_column_is_valid(column_types.DnaString.build("key", dna), dna)
        self.is_column_is_valid(
            column_types.NullableDnaString.build("key", ""), None, [None]
        )
        self.is_column_is_valid(
            column_types.NullableDnaString.build("key", "-"), "-", [None]
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.NullableDnaString.build("key", "ACGTN"),
            "ACGTN",
            "The 5th base in 'ACGTN' was not in [ACGT]",
        )
        self.is_column_invalid(
            column_types.NullableDnaString.build("key", "ACGTN"),
            1,
            "'1' was not a string",
        )
        self.is_column_invalid(
            column_types.DnaString.build("key", "ACGTN"),
            "ACGTN",
            "The 5th base in 'ACGTN' was not in [ACGT]",
        )
        self.is_column_invalid(
            column_types.DnaString.build("key", ""), "", "Found an empty string"
        )


class TestCanonical(TestCase):
    def test_valid(self):
        self.is_column_is_valid(column_types.Canonical.build("key", "YES"), True)
        self.is_column_is_valid(column_types.Canonical.build("key", "yes"), True)
        self.is_column_is_valid(column_types.Canonical.build("key", ""), False)

    def test_invalid(self):
        self.is_column_invalid(
            column_types.Canonical.build("key", "YES"), "YES", "was not a bool"
        )

        with self.assertRaises(ValueError):
            column_types.Canonical.build("key", "NO")

        with self.assertRaises(ValueError):
            column_types.Canonical.build("key", 1)


class TestNullableYesOrNo(TestCase):
    def test_valid(self):
        nulls = [
            column_values.NullableYesOrNoEnum.Null,
            column_values.NullableYesOrNoEnum.Null,
        ]
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "YES"),
            column_values.NullableYesOrNoEnum.Yes,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "yes"),
            column_values.NullableYesOrNoEnum.Yes,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "1"),
            column_values.NullableYesOrNoEnum.Yes,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "Null"),
            column_values.NullableYesOrNoEnum.Null,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "null"),
            column_values.NullableYesOrNoEnum.Null,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "NO"),
            column_values.NullableYesOrNoEnum.No,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "no"),
            column_values.NullableYesOrNoEnum.No,
            nulls,
        )
        self.is_column_is_valid(
            column_types.NullableYesOrNo.build("key", "0"),
            column_values.NullableYesOrNoEnum.No,
            nulls,
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.NullableYesOrNo.build("key", "YES"),
            "YES",
            "was not of type 'NullableYesOrNoEnum'",
        )

        with self.assertRaises(KeyError):
            column_types.NullableYesOrNo.build("key", "False")

        with self.assertRaises(ValueError):
            column_types.NullableYesOrNo.build("key", 1)


class TestBooleanColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "TRUE"), True)
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "True"), True)
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "true"), True)
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "FALSE"), False)
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "False"), False)
        self.is_column_is_valid(column_types.BooleanColumn.build("key", "false"), False)

    def test_invalid(self):
        self.is_column_invalid(
            column_types.BooleanColumn.build("key", "True"), "YES", "as not a bool"
        )

        with self.assertRaises(ValueError):
            column_types.BooleanColumn.build("key", "Foo")

        with self.assertRaises(ValueError):
            column_types.BooleanColumn.build("key", 1)


class TestEntrezGeneId(TestCase):
    def test_valid(self):
        self.is_column_is_valid(
            column_types.EntrezGeneId.build("key", "0"), None, [None]
        )
        self.is_column_is_valid(column_types.EntrezGeneId.build("key", "1"), 1, [None])
        self.assertEqual(str(column_types.EntrezGeneId.build("key", "0")), "0")
        self.assertIsNone(column_types.EntrezGeneId.build("key", "0").value)

    def test_invalid(self):
        self.is_column_invalid(
            column_types.EntrezGeneId.build("key", "0"), "YES", "was not an int"
        )

        with self.assertRaises(ValueError):
            column_types.EntrezGeneId.build("key", "Foo")

        with self.assertRaises(TypeError):
            column_types.EntrezGeneId.build("key", None)


class TestCustomEnums(TestCase):
    # These are all the custom Enum column classes we wish to test
    classes = [
        column_types.Strand,
        column_types.VariantClassification,
        column_types.VariantType,
        column_types.VerificationStatus,
        column_types.ValidationStatus,
        column_types.MutationStatus,
        column_types.Sequencer,
        column_types.FeatureType,
        column_types.Impact,
        column_types.MC3Overlap,
        column_types.GdcValidationStatus,
    ]

    def test_valid(self):
        for clazz in TestCustomEnums.classes:
            # Test every value in the Enum class
            enum_clazz = clazz.__enum_class__()
            for enum_value in enum_clazz:
                name = enum_value.name
                value = enum_value.value
                # Test both by name and by value
                self.is_column_is_valid(
                    clazz.build("key", str(name)),
                    enum_value,
                    clazz.__nullable_values__(),
                )
                self.is_column_is_valid(
                    clazz.build("key", value), enum_value, clazz.__nullable_values__()
                )

    def test_invalid(self):
        for clazz in TestCustomEnums.classes:
            # Test every value in the Enum class
            enum_clazz = clazz.__enum_class__()
            names = set([enum_value.name for enum_value in enum_clazz])
            values = set([enum_value.value for enum_value in enum_clazz])
            valid_values = names | values

            # Find an invalid value
            value = "Foo"
            while value in valid_values:
                value = value + "_"

            self.is_column_invalid(
                clazz.build("key", next(iter(valid_values))), value, "was not of type"
            )

            with self.assertRaises(KeyError):
                clazz.build("key", value)


class TestPickColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(
            column_types.PickColumn.build("key", "Null"),
            column_values.PickEnum.Null,
            column_types.PickColumn.__nullable_values__(),
        )
        self.is_column_is_valid(
            column_types.PickColumn.build("key", ""),
            column_values.PickEnum.Null,
            column_types.PickColumn.__nullable_values__(),
        )
        # self.is_column_is_valid(PickColumn.build("key", "None"), PickEnum.Null, PickColumn.__nullable_values__())
        self.is_column_is_valid(
            column_types.PickColumn.build("key", "Yes"),
            column_values.PickEnum.Yes,
            column_types.PickColumn.__nullable_values__(),
        )
        self.is_column_is_valid(
            column_types.PickColumn.build("key", "1"),
            column_values.PickEnum.Yes,
            column_types.PickColumn.__nullable_values__(),
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.PickColumn.build("key", "YES"),
            "YES",
            "was not of type 'PickEnum'",
        )

        with self.assertRaises(KeyError):
            column_types.PickColumn.build("key", "False")

        with self.assertRaises(ValueError):
            column_types.PickColumn.build("key", 1)


class TestSequenceOfSequencers(TestCase):
    def test_valid(self):
        self.is_column_is_valid(
            column_types.SequenceOfSequencers.build("key", "Illumina HiSeq"),
            [column_values.SequencerEnum.IlluminaHiSeq],
            column_types.SequenceOfSequencers.__nullable_values__(),
        )
        self.is_column_is_valid(
            column_types.SequenceOfSequencers.build("key", "AB SOLiD 4 System"),
            [column_values.SequencerEnum.ABSOLiDFourSystem],
            column_types.SequenceOfSequencers.__nullable_values__(),
        )
        sequencer_string = ";".join(["Illumina HiSeq", "AB SOLiD 4 System"])
        sequencers = [
            column_values.SequencerEnum.IlluminaHiSeq,
            column_values.SequencerEnum.ABSOLiDFourSystem,
        ]
        self.is_column_is_valid(
            column_types.SequenceOfSequencers.build("key", sequencer_string),
            sequencers,
            column_types.SequenceOfSequencers.__nullable_values__(),
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.SequenceOfSequencers.build("key", "AB SOLiD 4 System"),
            0,
            "was neither a list nor tuple",
        )
        self.is_column_invalid(
            column_types.SequenceOfSequencers.build("key", "AB SOLiD 4 System"),
            [0],
            "was not of type 'SequencerEnum'",
        )

        with self.assertRaises(KeyError):
            column_types.SequenceOfSequencers.build("key", "False")

        with self.assertRaises(ValueError):
            column_types.PickColumn.build("key", 1)


class TestUUIDColumn(TestCase):
    def test_valid(self):
        id = column_types.UUID('12345678-1234-5678-1234-567812345678')
        self.is_column_is_valid(column_types.UUIDColumn.build("key", str(id)), id)

        # Test the nullable version
        self.is_column_is_valid(
            column_types.NullableUUIDColumn.build("key", str(id)), id, [None]
        )
        self.is_column_is_valid(
            column_types.NullableUUIDColumn.build("key", "", id), None, [None]
        )

    def test_invalid(self):
        id = column_types.UUID('12345678-1234-5678-1234-567812345678')
        self.is_column_invalid(
            column_types.UUIDColumn.build("key", str(id)), "Foo", "was not a UUID"
        )
        self.is_column_invalid(
            column_types.UUIDColumn.build("key", str(id)), 0, "was not a UUID"
        )

        with self.assertRaises(ValueError):
            column_types.UUIDColumn.build("key", "1")

        with self.assertRaises(ValueError):
            column_types.UUIDColumn.build("key", "blah")

        with self.assertRaises(ValueError):
            column_types.UUIDColumn.build("key", "")


class TestTranscriptStrand(TestCase):
    def test_valid(self):
        self.is_column_is_valid(
            column_types.TranscriptStrand.build("key", "-1"),
            -1,
            column_types.TranscriptStrand.__nullable_values__(),
        )
        self.is_column_is_valid(
            column_types.TranscriptStrand.build("key", "1"),
            1,
            column_types.TranscriptStrand.__nullable_values__(),
        )

    def test_invalid(self):
        self.is_column_invalid(
            column_types.TranscriptStrand.build("key", "0"), "Foo", "was not an int"
        )
        self.is_column_invalid(
            column_types.TranscriptStrand.build("key", "0"), 0, "was neither -1 nor 1"
        )

        with self.assertRaises(ValueError):
            column_types.TranscriptStrand.build("key", "blah")


# __END__
