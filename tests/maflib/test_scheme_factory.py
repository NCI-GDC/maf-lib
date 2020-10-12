#!/usr/bin/env python3

import os
import unittest
from collections import OrderedDict

from maflib.column_types import IntegerColumn, RequireNullValue
from maflib.scheme_factory import (
    SchemeDatum,
    _Column,
    build_scheme_class,
    build_schemes,
    combine_columns,
    find_scheme_class,
    get_built_in_filenames,
    get_column_types,
    load_all_scheme_data,
    load_all_schemes,
    scheme_to_columns,
    validate_schemes,
)
from maflib.schemes import MafScheme, NoRestrictionsScheme
from tests.maflib.testutils import tmp_file


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
            return OrderedDict(
                [
                    ("Column1", IntegerColumn),
                    ("Column2", IntegerColumn),
                    ("Column3", IntegerColumn),
                ]
            )

        @classmethod
        def __column_desc__(cls):
            column_desc = super(TestSchemeFactory.TestBaseScheme, cls).__column_desc__()
            column_desc["Column1"] = "A description"
            return column_desc

    class TestExtendedScheme(TestBaseScheme):
        @classmethod
        def annotation_spec(cls):
            return "test-extended-annotation"

    datum1 = SchemeDatum(
        version="v1",
        annotation="v1",
        extends=None,
        columns=[
            _Column(name=k, cls=cls, desc="")
            for k, cls in TestBaseScheme.__column_dict__().items()
        ],
        filtered=None,
    )
    datum2 = SchemeDatum(
        version="v1",
        annotation="v1-protected",
        extends="v1",
        columns=[_Column(name="Column4", cls=IntegerColumn, desc="")],
        filtered=None,
    )
    datum3 = SchemeDatum(
        version="v1",
        annotation="v1-public",
        extends="v1",
        columns=[_Column(name="Column2", cls=RequireNullValue, desc="")],
        filtered=["Column3"],
    )

    datum_cycle1 = SchemeDatum(
        version="v1",
        annotation="v1-public",
        extends="v1-protected",
        columns=[("Column1", "IntegerColumn")],
        filtered=None,
    )
    datum_cycle2 = SchemeDatum(
        version="v1",
        annotation="v1-protected",
        extends="v1-public",
        columns=[("Column1", "IntegerColumn")],
        filtered=None,
    )

    def test_combine_columns(self):
        base_columns = scheme_to_columns(scheme=self.TestBaseScheme())
        extra_columns = [
            _Column(name="Column2", cls=RequireNullValue, desc="c2"),
            _Column(name="Column4", cls=IntegerColumn, desc="c4"),
        ]
        filtered = ["Column3"]

        # combine two dicts, add type to one column, and add a new column
        columns = combine_columns(
            base_columns=base_columns, extra_columns=extra_columns, filtered=None
        )
        self.assertTrue(len(columns), 4)
        self.assertListEqual(
            list([c.name for c in columns]),
            ["Column1", "Column2", "Column3", "Column4"],
        )
        self.assertListEqual(
            list([c.desc for c in columns]),
            ["A description", "c2", "No description for column 'Column3'", "c4"],
        )

        # filter a dict
        columns = combine_columns(
            base_columns=base_columns, extra_columns=None, filtered=filtered
        )
        self.assertTrue(len(columns), 2)
        self.assertListEqual(list([c.name for c in columns]), ["Column1", "Column2"])
        self.assertListEqual(
            list([c.desc for c in columns]),
            ["A description", "No description for column 'Column2'"],
        )
        # combine and filter
        columns = combine_columns(
            base_columns=base_columns, extra_columns=extra_columns, filtered=filtered
        )
        self.assertTrue(len(columns), 3)
        self.assertListEqual(
            list([c.name for c in columns]), ["Column1", "Column2", "Column4"]
        )
        self.assertListEqual(
            list([c.desc for c in columns]), ["A description", "c2", "c4"]
        )

        # filtered missing from base
        with self.assertRaises(ValueError):
            columns = combine_columns(
                base_columns=base_columns, extra_columns=None, filtered=["Column5"]
            )

    def test_build_scheme_class(self):
        # no columns
        datum = SchemeDatum(
            version="version",
            annotation="annotation",
            extends=None,
            columns=None,
            filtered=None,
        )
        scheme_cls = build_scheme_class(datum=datum, base_scheme=None)
        self.assertIsNotNone(scheme_cls)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), [])

        # a single column
        datum = SchemeDatum(
            version="version",
            annotation="annotation",
            extends=None,
            columns=[_Column(name="Column1", cls=IntegerColumn, desc="")],
            filtered=None,
        )
        scheme_cls = build_scheme_class(datum=datum, base_scheme=None)
        self.assertIsNotNone(scheme_cls)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), ["Column1"])
        self.assertEqual(scheme.column_class("Column1"), IntegerColumn)
        self.assertEqual(scheme.column_class("Column1"), IntegerColumn)

        # requires column2 to be null, removes column3, and adds column4
        columns = [
            _Column(name="Column2", cls=RequireNullValue, desc=""),
            _Column(name="Column4", cls=IntegerColumn, desc=""),
        ]
        base_scheme = TestSchemeFactory.TestBaseScheme()
        datum = SchemeDatum(
            version="version",
            annotation="annotation",
            extends=base_scheme.version(),
            columns=columns,
            filtered=["Column3"],
        )
        scheme_cls = build_scheme_class(datum=datum, base_scheme=base_scheme)
        scheme = scheme_cls()
        self.assertEqual(scheme.version(), "version")
        self.assertEqual(scheme.annotation_spec(), "annotation")
        self.assertListEqual(scheme.column_names(), ["Column1", "Column2", "Column4"])
        self.assertEqual(scheme.column_class("Column1"), IntegerColumn)
        self.assertTrue(issubclass(scheme.column_class("Column2"), IntegerColumn))
        self.assertTrue(issubclass(scheme.column_class("Column2"), RequireNullValue))
        self.assertEqual(scheme.column_class("Column4"), IntegerColumn)

    def test_build_schemes(self):
        data = [
            TestSchemeFactory.datum1,
            TestSchemeFactory.datum2,
            TestSchemeFactory.datum3,
        ]

        schemes = build_schemes(data=data)
        versions = [s.version() for s in schemes.values()]
        annotations = [s.annotation_spec() for s in schemes.values()]
        self.assertTrue(len(schemes), 3)
        self.assertListEqual(versions, ["v1", "v1", "v1"])
        self.assertListEqual(annotations, ["v1", "v1-protected", "v1-public"])
        validate_schemes(schemes=schemes.values())

        # two schemes that depend on each other
        data = [TestSchemeFactory.datum_cycle1, TestSchemeFactory.datum_cycle2]
        with self.assertRaises(ValueError):
            build_schemes(data=data)

    def test_validate_schemes(self):
        # one scheme
        schemes = [TestSchemeFactory.TestBaseScheme()]
        self.assertTrue(validate_schemes(schemes))

        # same scheme twice
        schemes = [
            TestSchemeFactory.TestBaseScheme(),
            TestSchemeFactory.TestBaseScheme(),
        ]
        with self.assertRaises(ValueError):
            self.assertTrue(validate_schemes(schemes))

        # two different schemes
        schemes = [
            TestSchemeFactory.TestBaseScheme(),
            TestSchemeFactory.TestExtendedScheme(),
        ]
        self.assertTrue(validate_schemes(schemes))

    def test_load_all_scheme_data(self):
        # silly test to make sure we can load ll the built-in scheme data
        filenames = get_built_in_filenames()
        data = load_all_scheme_data(
            filenames, column_types=TestSchemeFactory.column_types
        )
        self.assertTrue(len(data) > 1)

        # test malformed JSON
        fd, fn = tmp_file("blah blah")
        fd.close()
        with self.assertRaises(ValueError):
            load_all_schemes([fn])
        os.remove(fn)

        # no column types, so we can't find the column
        with self.assertRaises(ValueError) as e:
            data = load_all_scheme_data(filenames, column_types=[])
            self.assertTrue("Could not find a column type with name" in str(e))

    def test_load_all_schemes(self):
        # silly test to make sure we can load all the built-in schemes
        schemes = load_all_schemes()
        self.assertTrue(len(schemes) > 1)

    def test_find_scheme_class(self):
        scheme = find_scheme_class(
            NoRestrictionsScheme.version(), NoRestrictionsScheme.annotation_spec()
        )
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), NoRestrictionsScheme.version())
        self.assertEqual(
            scheme.annotation_spec(), NoRestrictionsScheme.annotation_spec()
        )
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
        scheme = find_scheme_class(
            version="gdc-1.0.0", annotation="gdc-1.0.0-protected"
        )
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.version(), "gdc-1.0.0")
        self.assertEqual(scheme.annotation_spec(), "gdc-1.0.0-protected")
        self.assertFalse(scheme.is_basic())
        self.assertEqual(len(scheme.__column_dict__()), 125)


# __END__
