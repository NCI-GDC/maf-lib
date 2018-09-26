import unittest

from maflib.column_types import *
from maflib.util import extend_class


class TestCase(unittest.TestCase):
    def is_column_is_valid(self, column, value, nullable_values=None):
        if nullable_values is None:
            self.assertIsNone(column.__nullable_values__())
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
        base_cls = NullableDnaString
        cls = extend_class(base_cls, RequireNullValue)

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
        self.is_column_is_valid(NullableStringColumn.build("key", "Foo"), "Foo", [None])
        self.is_column_is_valid(NullableStringColumn.build("key", ""), None,
                                [None])

    def test_invalid(self):
        self.is_column_invalid(NullableStringColumn.build("key", "Foo"), 2, "'2' was not a string")
        self.is_column_invalid(StringColumn.build("key", "Foo"), None,
                                   "'None' was not a string")

class TestStringColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(StringColumn.build("key", "Foo"), "Foo")

    def test_invalid(self):
        self.is_column_invalid(StringColumn.build("key", "Foo"), 2, "'2' was not a string")
        self.is_column_invalid(StringColumn.build("key", ""), "", StringColumn.EmptyStringMessage)
        self.is_column_invalid(StringColumn.build("key", "Foo"), None,
                               "'None' was not a string")


class TestStringIntegerOrFloatColumn(TestCase):
    def test_valid(self):
        for value in ["Foo", 2, 3.14]:
            self.is_column_is_valid(StringIntegerOrFloatColumn.build("key", value), value)

    def test_invalid(self):
        column = StringIntegerOrFloatColumn.build("key", "Foo")
        self.is_column_invalid(column, None, StringIntegerOrFloatColumn.__type_error_message__(None))

        with self.assertRaises(TypeError):
            StringIntegerOrFloatColumn.build("key", None)


class TestStringOrIntegerColumn(TestCase):
    def test_valid(self):
        for value in ["Foo", 2]:
            self.is_column_is_valid(StringOrIntegerColumn.build("key", value),
                                    value)

    def test_invalid(self):
        column = StringOrIntegerColumn.build("key", "Foo")
        self.is_column_invalid(column, None,
                               StringOrIntegerColumn.__type_error_message__(
                                   None))

        with self.assertRaises(TypeError):
            StringOrIntegerColumn.build("key", column)


class TestIntegerColumn(TestCase):

    class RangedIntegerColumn(IntegerColumn):
        @classmethod
        def __min_value__(cls):
            return -1

        @classmethod
        def __max_value__(cls):
            return 1

    def test_valid(self):
        self.is_column_is_valid(IntegerColumn.build("key", 1), 1)
        self.is_column_is_valid(IntegerColumn.build("key", 0), 0)

    def test_invalid(self):
        self.is_column_invalid(IntegerColumn.build("key", 1), "Foo",
                               IntegerColumn.__type_error_message__("Foo"))

        with self.assertRaises(ValueError):
            IntegerColumn.build("key", "")

        self.is_column_invalid(TestIntegerColumn.RangedIntegerColumn("key", -10), -10, "out of range (<")
        self.is_column_invalid(TestIntegerColumn.RangedIntegerColumn("key", 10), 10, "out of range (>")

    def test_zero_based(self):
        self.is_column_is_valid(ZeroBasedIntegerColumn.build("key", 0), 0)
        self.is_column_invalid(ZeroBasedIntegerColumn("key", -1), -1, "out of range (<")

    def test_one_based(self):
        self.is_column_is_valid(OneBasedIntegerColumn.build("key", 1), 1)
        self.is_column_invalid(OneBasedIntegerColumn("key", 0), 0, "out of range (<")


class TestNullableIntegerColumn(TestCase):

    class RangedIntegerColumn(NullableIntegerColumn):
        @classmethod
        def __min_value__(cls):
            return -1

        @classmethod
        def __max_value__(cls):
            return 1

    def test_valid(self):
        self.is_column_is_valid(NullableIntegerColumn.build("key", 1), 1, [None])
        self.is_column_is_valid(NullableIntegerColumn.build("key", 0), 0, [None])
        self.is_column_is_valid(NullableIntegerColumn.build("key", ""), None, [None])

    def test_invalid(self):
        self.is_column_invalid(NullableIntegerColumn.build("key", 1), "Foo",
                               NullableIntegerColumn.__type_error_message__("Foo"))
        self.is_column_invalid(TestNullableIntegerColumn.RangedIntegerColumn("key", -10), -10, "out of range (<")
        self.is_column_invalid(TestNullableIntegerColumn.RangedIntegerColumn("key", 10), 10, "out of range (>")

    def test_zero_based(self):
        self.is_column_is_valid(NullableZeroBasedIntegerColumn.build("key", 0), 0, [None])
        self.is_column_invalid(NullableZeroBasedIntegerColumn("key", -1), -1, "out of range (<")

    def test_one_based(self):
        self.is_column_is_valid(NullableOneBasedIntegerColumn.build("key", 1), 1, [None])
        self.is_column_invalid(NullableOneBasedIntegerColumn("key", 0), 0, "out of range (<")


class TestFloatColumn(TestCase):
    def test_valid(self):
        for value in [1, 3.14]:
            self.is_column_is_valid(FloatColumn.build("key", value), value)

    def test_invalid(self):
        self.is_column_invalid(FloatColumn.build("key", 1), "Foo", "was not a float")

        with self.assertRaises(ValueError):
            FloatColumn.build("key", "value")


class TestEnumColumn(TestCase):
    @unique
    class TestEnum(MafEnum):
        Foo = "1.Foo"
        Bar = "2.Bar"
        Null = "3.Null"

    class NullableEnumColumn(EnumColumn):
        @classmethod
        def __enum_class__(cls):
            return TestEnumColumn.TestEnum

        @classmethod
        def __nullable_dict__(cls):
            return {TestEnumColumn.TestEnum.Null.name:
                        TestEnumColumn.TestEnum.Null}

    class NotNullableEnumColumn(EnumColumn):
        @classmethod
        def __enum_class__(cls):
            return TestEnumColumn.TestEnum

    def test_valid(self):
        for value in ["Foo", "1.Foo"]:
            self.is_column_is_valid(TestEnumColumn.NullableEnumColumn.build("key", value),
                                    TestEnumColumn.TestEnum.Foo,
                                    [TestEnumColumn.TestEnum.Null])

            self.is_column_is_valid(TestEnumColumn.NotNullableEnumColumn.build("key", value),
                                    TestEnumColumn.TestEnum.Foo)

    def test_invalid(self):
        with self.assertRaises(KeyError):
            TestEnumColumn.NullableEnumColumn.build("key", "NoOne")

        self.is_column_invalid(TestEnumColumn.NullableEnumColumn.build("key", "Foo"),
                               "NoOne",
                               "was not of type 'TestEnum'")


class TestSequenceOfStrings(TestCase):
    def test_valid(self):
        for value in ["", "1", "1;2", "1;2;3"]:
            expected_value = value.split(";") if len(value) > 0 else []
            self.is_column_is_valid(SequenceOfStrings.build("key", value), expected_value, [[]])

    def test_invalid(self):
        self.is_column_invalid(SequenceOfStrings.build("key", "1"), 1, "was neither a list nor tuple")
        self.is_column_invalid(SequenceOfStrings.build("key", "1"), [1], "was not a string")

        with self.assertRaises(ValueError):
            SequenceOfStrings.build("key", 1)

        SequenceOfStrings.build("key", "1;2;3;")


class TestSequenceOfIntegers(TestCase):
    def test_valid(self):
        input_values = ["", "1", "1;2", "1;2;3"]
        expected_values = [[], [1], [1, 2], [1, 2, 3]]
        for in_value, exp_values in zip(input_values, expected_values):
            self.is_column_is_valid(SequenceOfIntegers.build("key", in_value), exp_values, [[]])
        self.is_column_is_valid(SequenceOfIntegers.build("key", ""), [], [[]])

    def test_invalid(self):
        self.is_column_invalid(SequenceOfIntegers.build("key", "1"), 1, "was neither a list nor tuple")
        self.is_column_invalid(SequenceOfIntegers.build("key", "1"), ["A"],
                               "For the 1th value in '['A']'")
        self.is_column_invalid(SequenceOfIntegers.build("key", "1"), ["1"],
                               "For the 1th value in '['1']'")

        with self.assertRaises(ValueError):
            SequenceOfIntegers.build("key", 1)

        with self.assertRaises(ValueError):
            SequenceOfIntegers.build("key", "1;A")

        with self.assertRaises(ValueError):
            SequenceOfIntegers.build("key", "1;A;")


class TestDnaString(TestCase):
    def test_valid(self):
        for dna in ["A", "ACGT", "GATTACA"]:
            self.is_column_is_valid(NullableDnaString.build("key", dna), dna, [None])
            self.is_column_is_valid(DnaString.build("key", dna), dna)
        self.is_column_is_valid(NullableDnaString.build("key", ""), None, [None])
        self.is_column_is_valid(NullableDnaString.build("key", "-"), "-", [None])

    def test_invalid(self):
        self.is_column_invalid(NullableDnaString.build("key", "ACGTN"), "ACGTN",
                               "The 5th base in 'ACGTN' was not in [ACGT]")
        self.is_column_invalid(NullableDnaString.build("key", "ACGTN"), 1, "'1' was not a string")
        self.is_column_invalid(DnaString.build("key", "ACGTN"), "ACGTN", "The 5th base in 'ACGTN' was not in [ACGT]")
        self.is_column_invalid(DnaString.build("key", ""), "", "Found an empty string")


class TestCanonical(TestCase):
    def test_valid(self):
        self.is_column_is_valid(Canonical.build("key", "YES"), True)
        self.is_column_is_valid(Canonical.build("key", "yes"), True)
        self.is_column_is_valid(Canonical.build("key", ""), False)

    def test_invalid(self):
        self.is_column_invalid(Canonical.build("key", "YES"), "YES", "was not a bool")

        with self.assertRaises(ValueError):
            Canonical.build("key", "NO")

        with self.assertRaises(ValueError):
            Canonical.build("key", 1)


class TestNullableYesOrNo(TestCase):
    def test_valid(self):
        nulls = [NullableYesOrNoEnum.Null, NullableYesOrNoEnum.Null]
        self.is_column_is_valid(NullableYesOrNo.build("key", "YES"), NullableYesOrNoEnum.Yes, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "yes"), NullableYesOrNoEnum.Yes, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "1"),
                                NullableYesOrNoEnum.Yes, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "Null"), NullableYesOrNoEnum.Null, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "null"), NullableYesOrNoEnum.Null, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "NO"), NullableYesOrNoEnum.No, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "no"), NullableYesOrNoEnum.No, nulls)
        self.is_column_is_valid(NullableYesOrNo.build("key", "0"),
                                NullableYesOrNoEnum.No, nulls)

    def test_invalid(self):
        self.is_column_invalid(NullableYesOrNo.build("key", "YES"), "YES", "was not of type 'NullableYesOrNoEnum'")

        with self.assertRaises(KeyError):
            NullableYesOrNo.build("key", "False")

        with self.assertRaises(ValueError):
            NullableYesOrNo.build("key", 1)


class TestBooleanColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(BooleanColumn.build("key", "TRUE"), True)
        self.is_column_is_valid(BooleanColumn.build("key", "True"), True)
        self.is_column_is_valid(BooleanColumn.build("key", "true"), True)
        self.is_column_is_valid(BooleanColumn.build("key", "FALSE"), False)
        self.is_column_is_valid(BooleanColumn.build("key", "False"), False)
        self.is_column_is_valid(BooleanColumn.build("key", "false"), False)

    def test_invalid(self):
        self.is_column_invalid(BooleanColumn.build("key", "True"), "YES", "as not a bool")

        with self.assertRaises(ValueError):
            BooleanColumn.build("key", "Foo")

        with self.assertRaises(ValueError):
            BooleanColumn.build("key", 1)


class TestEntrezGeneId(TestCase):
    def test_valid(self):
        self.is_column_is_valid(EntrezGeneId.build("key", "0"), None, [None])
        self.is_column_is_valid(EntrezGeneId.build("key", "1"), 1, [None])
        self.assertEqual(str(EntrezGeneId.build("key", "0")), "0")
        self.assertIsNone(EntrezGeneId.build("key", "0").value)

    def test_invalid(self):
        self.is_column_invalid(EntrezGeneId.build("key", "0"), "YES",
                               "was not an int")

        with self.assertRaises(ValueError):
            EntrezGeneId.build("key", "Foo")

        with self.assertRaises(TypeError):
            EntrezGeneId.build("key", None)


class TestCustomEnums(TestCase):
    # These are all the custom Enum column classes we wish to test
    classes = [
        Strand,
        VariantClassification,
        VariantType,
        VerificationStatus,
        ValidationStatus,
        MutationStatus,
        Sequencer,
        FeatureType,
        Impact,
        MC3Overlap,
        GdcValidationStatus
    ]

    def test_valid(self):
        for clazz in TestCustomEnums.classes:
            # Test every value in the Enum class
            enum_clazz = clazz.__enum_class__()
            for enum_value in enum_clazz:
                name = enum_value.name
                value = enum_value.value
                # Test both by name and by value
                self.is_column_is_valid(clazz.build("key", str(name)), enum_value, clazz.__nullable_values__())
                self.is_column_is_valid(clazz.build("key", value), enum_value, clazz.__nullable_values__())

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

            self.is_column_invalid(clazz.build("key", next(iter(valid_values))), value, "was not of type")

            with self.assertRaises(KeyError):
                clazz.build("key", value)


class TestPickColumn(TestCase):
    def test_valid(self):
        self.is_column_is_valid(PickColumn.build("key", "Null"), PickEnum.Null, PickColumn.__nullable_values__())
        self.is_column_is_valid(PickColumn.build("key", ""), PickEnum.Null, PickColumn.__nullable_values__())
        #self.is_column_is_valid(PickColumn.build("key", "None"), PickEnum.Null, PickColumn.__nullable_values__())
        self.is_column_is_valid(PickColumn.build("key", "Yes"), PickEnum.Yes, PickColumn.__nullable_values__())
        self.is_column_is_valid(PickColumn.build("key", "1"), PickEnum.Yes, PickColumn.__nullable_values__())

    def test_invalid(self):
        self.is_column_invalid(PickColumn.build("key", "YES"), "YES", "was not of type 'PickEnum'")

        with self.assertRaises(KeyError):
            PickColumn.build("key", "False")

        with self.assertRaises(ValueError):
            PickColumn.build("key", 1)


class TestSequenceOfSequencers(TestCase):
    def test_valid(self):
        self.is_column_is_valid(SequenceOfSequencers.build("key", "Illumina HiSeq"), [SequencerEnum.IlluminaHiSeq], SequenceOfSequencers.__nullable_values__())
        self.is_column_is_valid(SequenceOfSequencers.build("key", "AB SOLiD 4 System"), [SequencerEnum.ABSOLiDFourSystem], SequenceOfSequencers.__nullable_values__())
        sequencer_string = ";".join([
            "Illumina HiSeq",
            "AB SOLiD 4 System"
        ])
        sequencers = [
            SequencerEnum.IlluminaHiSeq,
            SequencerEnum.ABSOLiDFourSystem
        ]
        self.is_column_is_valid(SequenceOfSequencers.build("key", sequencer_string), sequencers, SequenceOfSequencers.__nullable_values__())

    def test_invalid(self):
        self.is_column_invalid(SequenceOfSequencers.build("key", "AB SOLiD 4 System"), 0, "was neither a list nor tuple")
        self.is_column_invalid(SequenceOfSequencers.build("key", "AB SOLiD 4 System"), [0], "was not of type 'SequencerEnum'")

        with self.assertRaises(KeyError):
            SequenceOfSequencers.build("key", "False")

        with self.assertRaises(ValueError):
            PickColumn.build("key", 1)


class TestUUIDColumn(TestCase):
    def test_valid(self):
        id = UUID('12345678-1234-5678-1234-567812345678')
        self.is_column_is_valid(UUIDColumn.build("key", str(id)), id)

        # Test the nullable version
        self.is_column_is_valid(NullableUUIDColumn.build("key", str(id)), id, [None])
        self.is_column_is_valid(NullableUUIDColumn.build("key", "", id), None, [None])

    def test_invalid(self):
        id = UUID('12345678-1234-5678-1234-567812345678')
        self.is_column_invalid(UUIDColumn.build("key", str(id)), "Foo", "was not a UUID")
        self.is_column_invalid(UUIDColumn.build("key", str(id)), 0, "was not a UUID")

        with self.assertRaises(ValueError):
            UUIDColumn.build("key", "1")

        with self.assertRaises(ValueError):
            UUIDColumn.build("key", "blah")

        with self.assertRaises(ValueError):
            UUIDColumn.build("key", "")

class TestTranscriptStrand(TestCase):
    def test_valid(self):
        self.is_column_is_valid(TranscriptStrand.build("key", "-1"), -1,
                                TranscriptStrand.__nullable_values__())
        self.is_column_is_valid(TranscriptStrand.build("key", "1"), 1,
                                TranscriptStrand.__nullable_values__())

    def test_invalid(self):
        self.is_column_invalid(TranscriptStrand.build("key", "0"), "Foo",
                               "was not an int")
        self.is_column_invalid(TranscriptStrand.build("key", "0"), 0, "was neither -1 nor 1")

        with self.assertRaises(ValueError):
            TranscriptStrand.build("key", "blah")
