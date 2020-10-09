import unittest
from collections import OrderedDict

from maflib.header import MafHeader, MafHeaderRecord, MafHeaderVersionRecord
from maflib.schemes import MafScheme, NoRestrictionsScheme
from maflib.tests.testutils import (
    GdcV1_0_0_BasicScheme,
    GdcV1_0_0_ProtectedScheme,
    GdcV1_0_0_PublicScheme,
)


class TestMafScheme(unittest.TestCase):
    class TestScheme(MafScheme):
        _Columns = [
            MafHeaderVersionRecord("test-scheme"),
            MafHeaderRecord("key1", "value1"),
        ]

        @classmethod
        def version(cls):
            return "test-scheme"

        @classmethod
        def annotation_spec(cls):
            return "test-annotation"

        @classmethod
        def __column_dict__(cls):
            return OrderedDict(
                [
                    (column.key, column.__class__)
                    for column in TestMafScheme.TestScheme._Columns
                ]
            )

        @classmethod
        def __column_desc__(cls):
            return OrderedDict(
                [
                    (column.key, str(column.__class__))
                    for column in TestMafScheme.TestScheme._Columns
                ]
            )

    def test_version(self):
        self.assertEqual(TestMafScheme.TestScheme().version(), "test-scheme")

    def test_column_class(self):
        scheme = TestMafScheme.TestScheme()
        self.assertEqual(
            scheme.column_class(MafHeader.VersionKey), MafHeaderVersionRecord
        )
        self.assertNotEqual(scheme.column_class("key1"), MafHeaderVersionRecord)
        self.assertEqual(scheme.column_class("key1"), MafHeaderRecord)
        self.assertEqual(scheme.column_class("key2"), None)

    def test_column_index(self):
        scheme = TestMafScheme.TestScheme()
        self.assertEqual(scheme.column_index(MafHeader.VersionKey), 0)
        self.assertEqual(scheme.column_index("key1"), 1)
        self.assertEqual(scheme.column_index("key2"), None)

    def test_column_description(self):
        scheme = TestMafScheme.TestScheme()
        self.assertEqual(
            scheme.column_description(MafHeader.VersionKey), str(MafHeaderVersionRecord)
        )
        self.assertEqual(scheme.column_description("key1"), str(MafHeaderRecord))
        self.assertEqual(scheme.column_description("key2"), None)

    def test_column_names(self):
        scheme = TestMafScheme.TestScheme()
        self.assertListEqual(scheme.column_names(), [MafHeader.VersionKey, "key1"])

    def test_column_descriptions(self):
        scheme = TestMafScheme.TestScheme()
        self.assertListEqual(
            scheme.column_descriptions(), [MafHeader.VersionKey, "key1"]
        )

    def test_str(self):
        scheme = TestMafScheme.TestScheme()
        self.assertEqual(str(scheme), scheme.version())


class TestNoRestrictionsScheme(unittest.TestCase):
    def test_no_columns(self):
        scheme = NoRestrictionsScheme(column_names=list())
        self.assertListEqual(scheme.column_names(), [])
        with self.assertRaises(ValueError):
            NoRestrictionsScheme.__column_dict__()


class TestGdcV1_0_0_Scheme(unittest.TestCase):
    class NoAnnotationSpecScheme(MafScheme):
        @classmethod
        def version(cls):
            return "test-scheme"

        @classmethod
        def annotation_spec(cls):
            return None

        @classmethod
        def __column_dict__(cls):
            return OrderedDict()

    def test_columns(self):
        self.assertEqual(len(GdcV1_0_0_BasicScheme.__column_dict__()), 34)
        self.assertEqual(len(GdcV1_0_0_PublicScheme.__column_dict__()), 119)
        self.assertEqual(len(GdcV1_0_0_ProtectedScheme.__column_dict__()), 125)
        self.assertEqual(
            len(TestGdcV1_0_0_Scheme.NoAnnotationSpecScheme.__column_dict__()), 0
        )

    def test_is_basic(self):
        self.assertTrue(GdcV1_0_0_BasicScheme().is_basic())
        self.assertFalse(GdcV1_0_0_PublicScheme().is_basic())
        self.assertFalse(GdcV1_0_0_ProtectedScheme().is_basic())
        self.assertFalse(TestGdcV1_0_0_Scheme.NoAnnotationSpecScheme().is_basic())

    def test_schemes(self):
        for scheme in [
            GdcV1_0_0_BasicScheme(),
            GdcV1_0_0_ProtectedScheme(),
            GdcV1_0_0_PublicScheme(),
        ]:
            # TODO: make up a valid string value for each column, and make sure it builds OK
            for name in scheme.column_names():
                cls = scheme.column_class(name)
                column_index = scheme.column_index(name)
                cls.build(name=name, value="Gene", column_index=column_index)
                break
