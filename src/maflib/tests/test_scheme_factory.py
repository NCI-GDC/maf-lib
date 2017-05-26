import os
import unittest
from collections import OrderedDict

from maflib.column_types import IntegerColumn, RequireNullValue
from maflib.scheme_factory import combine_column_dicts, get_column_types, \
    build_scheme_class, build_schemes, validate_schemes, SchemeDatum, \
    get_built_in_filenames, load_all_scheme_data, load_all_schemes, \
    find_scheme_class
from maflib.schemes import MafScheme, NoRestrictionsScheme
from maflib.tests.testutils import tmp_file


class TestSchemeFactory(unittest.TestCase):

    column_types = get_column_types()

    class TestBaseScheme(MafScheme):
        @classmethod
        def version(cls):
            return "test-base-scheme"

        @classmethod
        def annotation_spec(cls):
            return "test-base-annotation"

        @classmethod
        def __column_dict__(cls):
            return OrderedDict([("Column1", IntegerColumn),
                                ("Column2", IntegerColumn),
                                ("Column3", IntegerColumn)])

    class TestExtendedScheme(TestBaseScheme):
        @classmethod
        def annotation_spec(cls):
            return "test-extended-annotation"


    datum1 = SchemeDatum(version="v1", annotation="v1", extends=None,
                         columns=[(k, cls.__name__) for k, cls in \
                                  TestBaseScheme.__column_dict__().items()],
                         filtered = None)
    datum2 = SchemeDatum(version="v1", annotation="v1-protected", extends="v1",
                         columns=[("Column4", "IntegerColumn")],
                         filtered = None)
    datum3 = SchemeDatum(version="v1", annotation="v1-public", extends="v1",
                         columns=[("Column2", "RequireNullValue")],
                         filtered = ["Column3"])

    datum_cycle1 = SchemeDatum(version="v1", annotation="v1-public",
                               extends="v1-protected",
                               columns=[("Column1", "IntegerColumn")],
                               filtered=None)
    datum_cycle2 = SchemeDatum(version="v1", annotation="v1-protected",
                               extends="v1-public",
                               columns=[("Column1", "IntegerColumn")],
                               filtered=None)

    def test_combine_column_dicts(self):
        base_dict = self.TestBaseScheme.__column_dict__()
        extra_dict = {
            "Column2": RequireNullValue,
            "Column4": IntegerColumn
        }
        filtered = ["Column3"]

        # combine two dicts, add type to one column, and add a new column
        dict = combine_column_dicts(
            base_dict=base_dict,
            extra_dict=extra_dict,
            filtered=None
        )
        self.assertTrue(len(dict), 4)
        self.assertListEqual(list(dict.keys()),
                             ["Column1", "Column2", "Column3", "Column4"])

        # filter a dict
        dict = combine_column_dicts(
            base_dict=base_dict,
            extra_dict=None,
            filtered=filtered
        )
        self.assertTrue(len(dict), 2)
        self.assertListEqual(list(dict.keys()), ["Column1", "Column2"])

        # combine and filter
        dict = combine_column_dicts(
            base_dict=base_dict,
            extra_dict=extra_dict,
            filtered=filtered
        )
        self.assertTrue(len(dict), 3)
        self.assertListEqual(list(dict.keys()),
                                  ["Column1", "Column2", "Column4"])

    def test_build_scheme_class(self):
        # no columns
        datum = SchemeDatum(version="version",
                            annotation="annotation",
                            extends=None,
                            columns=None,
                            filtered=None)
        scheme_cls = build_scheme_class(datum=datum,
                                        base_scheme=None,
                                        column_types=TestSchemeFactory.column_types)
        self.assertIsNotNone(scheme_cls)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), [])

        # a single column
        datum = SchemeDatum(version="version",
                            annotation="annotation",
                            extends=None,
                            columns=[("Column1", "IntegerColumn")],
                            filtered=None)
        scheme_cls = build_scheme_class(datum=datum,
                                        base_scheme=None,
                                        column_types=TestSchemeFactory.column_types)
        self.assertIsNotNone(scheme_cls)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), ["Column1"])
        self.assertEqual(scheme.column_class("Column1").__class__,
                         IntegerColumn.__class__)
        self.assertEqual(scheme.column_class("Column1"), IntegerColumn)

        # requires column2 to be null, removes column3, and adds column4
        columns = [
            ("Column2", "RequireNullValue"),
            ("Column4", "IntegerColumn")
        ]
        base_scheme = TestSchemeFactory.TestBaseScheme()
        datum = SchemeDatum(version="version",
                            annotation="annotation",
                            extends=base_scheme.version(),
                            columns=columns,
                            filtered=["Column3"])
        scheme_cls = build_scheme_class(datum=datum,
                                        base_scheme=base_scheme,
                                        column_types=TestSchemeFactory.column_types)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), ["Column1", "Column2",
                                                     "Column4"])
        self.assertEqual(scheme.column_class("Column1").__class__,
                         IntegerColumn.__class__)
        self.assertEqual(scheme.column_class("Column2").__class__,
                         IntegerColumn.__class__)
        self.assertEqual(scheme.column_class("Column4").__class__,
                         IntegerColumn.__class__)

        # column type not found
        # a single column
        datum = SchemeDatum(version="version",
                            annotation="annotation",
                            extends=None,
                            columns=[("Column1", "FooBar")],
                            filtered=None)
        with self.assertRaises(ValueError):
            build_scheme_class(
                datum=datum,
                base_scheme=None,
                column_types=TestSchemeFactory.column_types)

    def test_build_schemes(self):
        data = [TestSchemeFactory.datum1, TestSchemeFactory.datum2,
                TestSchemeFactory.datum3]

        schemes = build_schemes(data=data,
                                column_types=TestSchemeFactory.column_types)
        versions = [s.version() for s in schemes.values()]
        annotations = [s.annotation_spec() for s in schemes.values()]
        self.assertTrue(len(schemes), 3)
        self.assertListEqual(versions, ["v1", "v1", "v1"])
        self.assertListEqual(annotations, ["v1", "v1-protected", "v1-public"])
        validate_schemes(schemes=schemes.values())

        # no column types
        with self.assertRaises(ValueError):
            build_schemes(data=[TestSchemeFactory.datum1],
                          column_types=[])

        # two schemes that depend on each other
        data = [TestSchemeFactory.datum_cycle1, TestSchemeFactory.datum_cycle2]
        with self.assertRaises(ValueError):
            build_schemes(data=data,
                          column_types=TestSchemeFactory.column_types)

    def test_validate_schemes(self):
        # one scheme
        schemes = [TestSchemeFactory.TestBaseScheme()]
        self.assertTrue(validate_schemes(schemes))

        # same scheme twice
        schemes = [TestSchemeFactory.TestBaseScheme(),
                   TestSchemeFactory.TestBaseScheme()]
        with self.assertRaises(ValueError):
            self.assertTrue(validate_schemes(schemes))

        # two different schemes
        schemes = [TestSchemeFactory.TestBaseScheme(),
                   TestSchemeFactory.TestExtendedScheme()]
        self.assertTrue(validate_schemes(schemes))

    def test_load_all_scheme_data(self):
        # silly test to make sure we can load ll the built-in scheme data
        filenames = get_built_in_filenames()
        data = load_all_scheme_data(filenames)
        self.assertTrue(len(data) > 1)

        # test malformed JSON
        fd, fn = tmp_file("blah blah")
        fd.close()
        with self.assertRaises(ValueError):
            load_all_schemes([fn])
        os.remove(fn)

    def test_load_all_schemes(self):
        # silly test to make sure we can load all the built-in schemes
        schemes = load_all_schemes()
        self.assertTrue(len(schemes) > 1)

    def test_find_scheme_class(self):
        scheme = find_scheme_class(NoRestrictionsScheme.version(),
                                   NoRestrictionsScheme.annotation_spec())
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), NoRestrictionsScheme.version())
        self.assertEqual(scheme.annotation_spec(),
                         NoRestrictionsScheme.annotation_spec())
        self.assertFalse(scheme.is_basic())
        with self.assertRaises(ValueError):
            scheme.__column_dict__()
        #
        scheme = find_scheme_class("gdc-1.0.0")
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), "gdc-1.0.0")
        self.assertEqual(scheme.annotation_spec(), "gdc-1.0.0")
        self.assertTrue(scheme.is_basic())
        self.assertEqual(len(scheme.__column_dict__()), 34)
        #
        #
        scheme = find_scheme_class(annotation="gdc-1.0.0-public")
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), "gdc-1.0.0")
        self.assertEqual(scheme.annotation_spec(), "gdc-1.0.0-public")
        self.assertFalse(scheme.is_basic())
        self.assertEqual(len(scheme.__column_dict__()), 119)
        #
        scheme = find_scheme_class(version="gdc-1.0.0",
                                   annotation="gdc-1.0.0-protected")
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), "gdc-1.0.0")
        self.assertEqual(scheme.annotation_spec(), "gdc-1.0.0-protected")
        self.assertFalse(scheme.is_basic())
        self.assertEqual(len(scheme.__column_dict__()), 125)
