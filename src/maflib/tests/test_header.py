import os
import tempfile
import unittest

from maflib.header import *
from maflib.reader import MafReader
from maflib.schemes import *
from maflib.tests.testutils import tmp_file, GdcV1_0_0_PublicScheme, \
    GdcV1_0_0_ProtectedScheme, GdcV1_0_0_BasicScheme
from maflib.util import LineReader
from maflib.validation import MafFormatException


class TestMafHeaderRecord(unittest.TestCase):

    def __test_from_line_with_error(self, lines, tpe):
        """
        A helper method for testing when MafHeaderRecord.from_line returns an error.
        """
        for line in lines:
            record, error = MafHeaderRecord.from_line(line=line)
            self.assertIsNone(record)
            self.assertIsNotNone(error)
            self.assertEqual(error.tpe, tpe)

    def test_from_line_missing_line_start_symbol(self):
        self.__test_from_line_with_error(
            lines=["", "@", " ", "ABCD"],
            tpe=MafValidationErrorType.HEADER_LINE_MISSING_START_SYMBOL
        )

    def test_from_line_missing_separator(self):
        self.__test_from_line_with_error(
            lines=["#abcdefg", "#abcdef\tg"],
            tpe=MafValidationErrorType.HEADER_LINE_MISSING_SEPARATOR
        )

    def test_from_line_empty_key(self):
        self.__test_from_line_with_error(
            lines=["# value", "#  value"],
            tpe=MafValidationErrorType.HEADER_LINE_EMPTY_KEY
        )

    def test_from_line_empty_value(self):
        self.__test_from_line_with_error(
            lines=["#key ", "#key ", "#key  ", "#key \t"],
            tpe=MafValidationErrorType.HEADER_LINE_EMPTY_VALUE
        )

    def test_from_line_version_record(self):
        """
        Tests that a MafHeaderVersionRecord is returned from MafHeaderRecord.from_line only when it encounters
        MafHeader.VersionKey.
        """
        for line in ["#%s %s" % (MafHeader.VersionKey, version) for version in MafHeader.SupportedVersions]:
            record, error = MafHeaderRecord.from_line(line=line)
            self.assertIsNotNone(record)
            self.assertIsNone(error)
            self.assertTrue(isinstance(record, MafHeaderVersionRecord))
            self.assertTrue(isinstance(record, MafHeaderRecord))

        for line in ["#garbage value", "#%sz value"]:
            record, error = MafHeaderRecord.from_line(line=line)
            self.assertIsNotNone(record)
            self.assertIsNone(error)
            self.assertFalse(isinstance(record, MafHeaderVersionRecord))
            self.assertTrue(isinstance(record, MafHeaderRecord))

    def test_from_line_trim_whitespace_at_the_end_of_value(self):
        for line in ["#key value ", "#key value  ", "#key value\t"]:
            record, error = MafHeaderRecord.from_line(line=line)
            self.assertIsNotNone(record)
            self.assertIsNone(error)
            self.assertFalse(isinstance(record, MafHeaderVersionRecord))
            self.assertTrue(isinstance(record, MafHeaderRecord))
            self.assertEqual(record.key, "key")
            self.assertEqual(record.value, "value")

    def test_get_and_set(self):
        record = MafHeaderRecord("key", "value")
        self.assertEqual(record.key, "key")
        self.assertEqual(record.value, "value")

        record.key = "key2"
        record.value = "value2"
        self.assertEqual(record.key, "key2")
        self.assertEqual(record.value, "value2")

    def test_str(self):
        record = MafHeaderRecord("key", "value")
        self.assertEqual(str(record), "#key value")

        record.key = "key2"
        record.value = "value2"
        self.assertEqual(str(record), "#key2 value2")

        record.key = " key2"
        record.value = " value2"
        self.assertEqual(str(record), "# key2  value2")

class TestMafHeader(unittest.TestCase):

    Scheme = GdcV1_0_0_ProtectedScheme()
    Version = Scheme.version()
    AnnotationSpec = Scheme.annotation_spec()

    __version_line = "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, Version)
    __annotation_line = "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.AnnotationSpecKey, AnnotationSpec)

    def test_from_line_reader_ok(self):
        fh, fn = tmp_file([TestMafHeader.__version_line, TestMafHeader.__annotation_line, "#key1 value1", "#key2 value2"])
        line_reader = LineReader(fh)
        header = MafHeader.from_line_reader(line_reader=line_reader, validation_stringency=ValidationStringency.Silent)
        fh.close()

        self.assertTrue(len(header.validation_errors) == 0)
        self.assertTrue(len(header) == 4)
        self.assertEqual(list(header.keys()),
                         [MafHeader.VersionKey,  MafHeader.AnnotationSpecKey,
                          "key1", "key2"])
        self.assertEqual([str(record.value) for record in header.values()],
                         [TestMafHeader.Version, TestMafHeader.AnnotationSpec, "value1", "value2"])
        self.assertEqual(header.version(), TestMafHeader.Version)
        os.remove(fn)

    def test_from_lines_duplicate_keys(self):
        lines = [TestMafHeader.__version_line, TestMafHeader.__annotation_line, "#dupkey value", "#dupkey value"]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

        self.assertTrue(len(header.validation_errors) == 1)
        self.assertIn("dupkey", str(header.validation_errors[0]))
        self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_DUPLICATE_KEYS)

    def test_from_lines_missing_version(self):
        lines = [TestMafHeader.__annotation_line, "#key1 value", "#key2 value"]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

        self.assertTrue(len(header.validation_errors) == 1)
        self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_MISSING_VERSION)
        self.assertIsNone(header.version())
        self.assertIsNotNone(header.scheme())
        self.assertIsNotNone(header.scheme().version())
        self.assertIsNotNone(header.scheme().annotation_spec())

    def test_from_lines_unsupported_version(self):
        for line in [
            "#%s not_version" % MafHeader.VersionKey,
            "#%s %sx" % (MafHeader.VersionKey, TestMafHeader.Version)
        ]:
            lines = [line, TestMafHeader.__annotation_line]
            header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

            self.assertTrue(len(header.validation_errors) == 1)
            self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_UNSUPPORTED_VERSION)
            self.assertIsNotNone(header.version())
            self.assertIsNone(header.scheme())

    def test_from_lines_default_to_basic(self):
        lines = [TestMafHeader.__version_line, "#key1 value", "#key2 value"]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)
        self.assertEqual(len(header.validation_errors), 0)
        self.assertIsNone(header.annotation())
        self.assertIsNotNone(header.scheme())
        self.assertIsNotNone(header.scheme().annotation_spec())

    def test_from_lines_missing_annotation(self):
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, NoRestrictionsScheme.version()),
                 "#key1 value", "#key2 value"]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)
        self.assertEqual(len(header.validation_errors), 1)
        self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_MISSING_ANNOTATION_SPEC)
        self.assertIsNone(header.annotation())
        self.assertIsNone(header.scheme())

    def test_from_lines_unsupported_annotation(self):
        scheme = GdcV1_0_0_BasicScheme()
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, scheme.version()),
                 "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.AnnotationSpecKey, scheme.annotation_spec())]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

        self.assertTrue(len(header.validation_errors) == 1)
        self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC)
        self.assertIsNotNone(header.annotation())
        self.assertIsNotNone(header.scheme())

        for line in [
            "#%s not_annotation" % MafHeader.AnnotationSpecKey,
            "#%s %sx" % (MafHeader.AnnotationSpecKey, TestMafHeader.AnnotationSpec)
        ]:
            lines = [TestMafHeader.__version_line, line]
            header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

            self.assertTrue(len(header.validation_errors) == 1)
            self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_UNSUPPORTED_ANNOTATION_SPEC)
            self.assertIsNotNone(header.annotation())
            self.assertIsNone(header.scheme())

    def test_from_lines_supported_annotation(self):
        scheme = GdcV1_0_0_ProtectedScheme()
        lines = ["%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.VersionKey, scheme.version()),
                 "%s%s %s" % (MafHeader.HeaderLineStartSymbol, MafHeader.AnnotationSpecKey, scheme.annotation_spec())]
        header = MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Silent)

        self.assertTrue(len(header.validation_errors) == 0)
        self.assertEqual(header.version(), scheme.version())
        self.assertEqual(header.annotation(), scheme.annotation_spec())
        self.assertEqual(header.scheme().version(), scheme.version())
        self.assertEqual(header.scheme().annotation_spec(), scheme.annotation_spec())

    def test_from_lines_strict_raises_on_error(self):
        """
        Checks that the first error encountered is raised.
        """
        lines = ["#key1 value", "#key1 value"]
        with self.assertRaises(MafFormatException) as context:
            MafHeader.from_lines(lines=lines, validation_stringency=ValidationStringency.Strict)

        self.assertIn("Multiple header lines", str(context.exception))
        self.assertEqual(context.exception.tpe, MafValidationErrorType.HEADER_DUPLICATE_KEYS)

    def __test_from_lines_lenient_or_silent(self, validation_stringency):
        """
        Checks that all errors are either printed out (Lenient) or not (Silent), and that a header is returned *without*
        the header lines that caused an error.
        """
        self.assertIn(validation_stringency, [ValidationStringency.Silent, ValidationStringency.Lenient])
        lines = [TestMafHeader.__version_line, TestMafHeader.__annotation_line,
                 "#key1 value1", "#key1 value2", "#key2 value3", "#key2 value4"]
        err_stream = tempfile.NamedTemporaryFile(delete=False, mode="w")
        err_file_name = err_stream.name
        logger = Logger.get_logger(err_file_name, stream=err_stream)
        header = MafHeader.from_lines(
            lines=lines,
            validation_stringency=validation_stringency,
            logger=logger
        )
        err_stream.close()

        reader = open(err_file_name, "r")
        actual_lines = reader.readlines()
        expected_lines = ["Multiple header lines with key 'key1' found", "Multiple header lines with key 'key2' found"]
        reader.close()
        os.remove(err_file_name)

        if validation_stringency == ValidationStringency.Lenient:
            self.assertTrue(len(actual_lines) == len(expected_lines))
            [self.assertIn(expected, actual) for (actual, expected) in zip(actual_lines, expected_lines)]
        else:
            self.assertTrue(len(actual_lines) == 0)

        self.assertTrue(len(header) == 4)
        self.assertListEqual(list(header.keys()), [MafHeader.VersionKey,
                               MafHeader.AnnotationSpecKey, "key1", "key2"])
        self.assertEqual([str(record.value) for record in header.values()],
                         [TestMafHeader.Version,TestMafHeader.AnnotationSpec, "value1", "value3"])
        for record, clzz in zip(header.values(), [MafHeaderVersionRecord, MafHeaderRecord, MafHeaderRecord]):
            self.assertTrue(isinstance(record, clzz))

    def test_from_lines_lenient_prints_all_errors(self):
        """
        Checks that all errors are printed out and a header is returned *without* the header lines that caused an error.
        """
        #self.__test_from_lines_lenient_or_silent(validation_stringency=ValidationStringency.Lenient)
        # FIXME: prints to stderr
        pass

    def test_from_lines_ignores_errors(self):
        """
        Checks that all errors squashed and a header is returned *without* the header lines that caused an error.
        """
        self.__test_from_lines_lenient_or_silent(validation_stringency=ValidationStringency.Silent)

    def test_from_lines_misformatted_line(self):
        lines = [TestMafHeader.__version_line, TestMafHeader.__annotation_line, "key1 value1"]
        header = MafHeader.from_lines(
            lines=lines,
            validation_stringency=ValidationStringency.Silent
        )
        self.assertEqual(len(header), 2)
        self.assertEqual(len(header.validation_errors), 1)
        self.assertEqual(header.validation_errors[0].tpe, MafValidationErrorType.HEADER_LINE_MISSING_START_SYMBOL)

    def test_dict_methods(self):
        """
        Checks that the header is well-behaved for a Mapping
        """
        version = MafHeaderRecord(MafHeader.VersionKey, TestMafHeader.Version)
        record1 = MafHeaderRecord("key1", "value1")
        record2 = MafHeaderRecord("key1", "value2")
        header = MafHeader()

        # Set version
        self.assertNotIn(version.key, header)
        header[version.key] = version
        self.assertIn(version.key, header)
        self.assertTrue(len(header) == 1)
        self.assertListEqual(list(header.keys()), [MafHeader.VersionKey])
        self.assertTrue(header.values(), [TestMafHeader.Version])
        self.assertEqual(header.version(), TestMafHeader.Version)
        expected_scheme = GdcV1_0_0_BasicScheme()
        self.assertEqual(header.scheme().version(), expected_scheme.version())
        self.assertEqual(header.scheme().annotation_spec(), expected_scheme.annotation_spec())

        # Set when it is not in the header
        self.assertNotIn(record1.key, header)
        header[record1.key] = record1
        self.assertIn(record1.key, header)
        self.assertTrue(len(header) == 2)
        self.assertListEqual(list(header.keys()), [MafHeader.VersionKey,
                                                   "key1"])
        self.assertTrue(header.values(), [TestMafHeader.Version, "value1"])

        # Overwrite
        self.assertIn(record2.key, header)
        header[record2.key] = record2
        self.assertIn(record2.key, header)
        self.assertTrue(len(header) == 2)
        self.assertListEqual(list(header.keys()), [MafHeader.VersionKey,
                                                   "key1"])
        self.assertTrue(header.values(), [TestMafHeader.Version, "value2"])

        # Remove it
        del header[record2.key]
        self.assertNotIn(record2.key, header)
        self.assertTrue(len(header) == 1)
        self.assertListEqual(list(header.keys()), [MafHeader.VersionKey])
        self.assertTrue(header.values(), [TestMafHeader.Version])

    def test_str(self):
        version = MafHeaderRecord(MafHeader.VersionKey, TestMafHeader.Version)
        record1 = MafHeaderRecord("key1", "value1")
        record2 = MafHeaderRecord("key2", "value2")
        header = MafHeader()

        version_line = "%s%s %s" % (MafHeader.HeaderLineStartSymbol,
                                   MafHeader.VersionKey,
                                   TestMafHeader.Version)
        record1_line = "%s%s %s" % (MafHeader.HeaderLineStartSymbol,
                                    record1.key, record1.value)
        record2_line = "%s%s %s" % (MafHeader.HeaderLineStartSymbol,
                                    record2.key, record2.value)

        self.assertEqual(str(header), "")

        header[version.key] = version
        self.assertEqual(str(header), version_line)

        header[record1.key] = record1
        self.assertEqual(str(header), "%s\n%s" % (version_line, record1_line))

        header[record2.key] = record2
        self.assertEqual(str(header), "%s\n%s\n%s" % (version_line,
                                                      record1_line,
                                                      record2_line))

    def test_from_reader(self):
        scheme = GdcV1_0_0_ProtectedScheme()

        lines = [
            TestMafHeader.__version_line,
            TestMafHeader.__annotation_line
        ]
        reader = MafReader(lines=lines,
                           validation_stringency=ValidationStringency.Silent,
                           scheme=scheme)
        reader.close()

        # No overrides
        header = MafHeader.from_reader(reader=reader)
        self.assertEqual(header.scheme().version(), scheme.version())
        self.assertEqual(header.scheme().annotation_spec(),
                         scheme.annotation_spec())

        # Override version and annotation
        scheme = GdcV1_0_0_PublicScheme()
        header = MafHeader.from_reader(reader=reader,
                                       version=scheme.version(),
                                       annotation=scheme.annotation_spec())
        self.assertEqual(header.scheme().version(), scheme.version())
        self.assertEqual(header.scheme().annotation_spec(),
                         scheme.annotation_spec())

    def test_scheme_header_lines(self):
        scheme = TestMafHeader.Scheme
        self.assertListEqual(MafHeader.scheme_header_lines(scheme),
                             [TestMafHeader.__version_line,
                              TestMafHeader.__annotation_line])

    # TODO: get the version with an empty header
