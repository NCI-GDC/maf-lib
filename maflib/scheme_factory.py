"""Module for building schemes"""

import glob
import json
import os
import re
from collections import OrderedDict, namedtuple

from maflib.column_types import get_column_types
from maflib.schemes import MafScheme, NoRestrictionsScheme
from maflib.util import extend_class

SchemeDatum = namedtuple(
    "SchemeDatum", ["version", "annotation", "extends", "columns", "filtered"]
)

_Column = namedtuple("_Column", ["name", "cls", "desc"])


def scheme_to_columns(scheme):
    """Creates a list of columns of type `_Column` from a scheme."""
    columns = list()
    names = scheme.column_names()
    for i in range(len(names)):
        name = names[i]
        column = _Column(
            name=name,
            cls=scheme.column_class(name),
            desc=scheme.column_description(name),
        )
        columns.append(column)
    return columns


def combine_columns(base_columns, extra_columns=None, filtered=None):
    """Combines columns when building a scheme.

    The `base_columns` and `extra_columns` should be a list of columns (of
    type `_Column`).

    Any columns in `extra_columns` that are also in `base_columns` will have
    the column class from `extra_columns` mixed into `base_columns`.  New
    columns from `extra_columns` will be appended.  The description will be
    kept from `extra_columns`.

    `filtered` can be used to _remove_ any columns from either the
    `base_columns` or the `extra_columns` after they are combined.
    """

    columns = OrderedDict((c.name, c) for c in base_columns)

    if extra_columns:
        # add any additional types to the base columns
        for extra_column in extra_columns:
            name = extra_column.name
            if name in columns:
                cls = extend_class(columns[name].cls, extra_column.cls)
                desc = extra_column.desc
                columns[name] = _Column(name=name, cls=cls, desc=desc)

        # add the extra_columns
        columns.update([(c.name, c) for c in extra_columns if c.name not in columns])

    if filtered is not None:
        missing_filtered = [f for f in filtered if f not in columns]
        if missing_filtered:
            raise ValueError(
                "Filtered columns not found in the scheme it "
                "extends: %s" % ", ".join(missing_filtered)
            )
        filtered_columns = OrderedDict()
        for name, column in columns.items():
            if name not in filtered:
                filtered_columns[name] = column
        columns = filtered_columns
    return columns.values()


def build_scheme_class(datum, base_scheme):
    """
    :param datum: a scheme datum class
    :param base_scheme: the base scheme, or None if no base scheme
    :return: a new MafScheme
    """

    columns = datum.columns if datum.columns else list()

    # extend the base scheme if necessary
    if base_scheme:
        base_columns = list()
        for name, cls in base_scheme.__column_dict__().items():
            base_column = _Column(
                name=name, cls=cls, desc=base_scheme.__column_desc__()[name]
            )
            base_columns.append(base_column)
        columns = combine_columns(
            base_columns=base_columns, extra_columns=columns, filtered=datum.filtered
        )
    else:
        columns = datum.columns

    name = "_".join([x.capitalize() for x in re.split(r"[-.]", datum.annotation)])

    if columns:
        column_dict = OrderedDict((c.name, c.cls) for c in columns)
        column_desc = OrderedDict((c.name, c.desc) for c in columns)
    else:
        column_dict = OrderedDict()
        column_desc = OrderedDict()

    # now create the scheme
    tpe = type(str(name), (MafScheme,), {})
    setattr(tpe, "version", classmethod(lambda cls: datum.version))
    setattr(tpe, "annotation_spec", classmethod(lambda cls: datum.annotation))
    setattr(tpe, "__column_dict__", classmethod(lambda cls: column_dict))
    setattr(tpe, "__column_desc__", classmethod(lambda cls: column_desc))

    return tpe


def build_schemes(data):
    """
    Builds the schemes represented by the list of ``SchemeDatum``s.
    :return: a mapping from the scheme annotation to the scheme
    """
    schemes = OrderedDict()  # annotation -> scheme
    while data:
        # find a scheme data that either doesn't extend any other scheme, or
        # whose base scheme it extends we have already built
        datum_index, datum = next(
            (
                (i, d)
                for (i, d) in enumerate(data)
                if not d.extends or d.extends in schemes
            ),
            (None, None),
        )
        if not datum:
            annotations = ", ".join([d.annotation for d in data])
            raise ValueError(
                "Could not find a scheme to build.  Schemes "
                "remaining annotations were: %s" % annotations
            )
        scheme_cls = build_scheme_class(
            datum=datum, base_scheme=schemes.get(datum.extends)
        )
        schemes[scheme_cls.annotation_spec()] = scheme_cls
        del data[datum_index]
    return schemes


def validate_schemes(schemes):
    """Validate that all schemes have different combinations of version
    and annotations
    """
    schemes = list(schemes)
    num_schemes = len(schemes)
    for i in range(num_schemes - 1):
        left = schemes[i]
        for j in range(i + 1, num_schemes):
            right = schemes[j]
            if (
                left.version() == right.version()
                and left.annotation_spec() == right.annotation_spec()
            ):
                raise ValueError(
                    "Two schemes found with version '%s' and "
                    "annotation specification '%s'"
                    % (str(left.version()), str(left.annotation_spec()))
                )

    return True


def get_built_in_filenames(filename=None):
    """
    Gets all the scheme filenames for built in schemes.
    """
    if not filename:
        filename = __file__
    path = os.path.join(os.path.dirname(filename), "schemas")  # TODO: Fixme
    return glob.glob(os.path.join(path, "*json"))


def load_all_scheme_data(filenames, column_types):
    """
    Load all the scheme data from the json file names
    :param filenames: a list of filenames for the json schemes
    :param column_types: a tuple of (name, class) for all known column types
    :return: a list of ``SchemeDatum`` objects
    """

    def else_none(value):
        return None if value == "None" else value

    data = []
    for filename in filenames:
        with open(filename) as handle:
            try:
                json_data = json.load(handle)
                handle.close()
                columns = list()
                for column in json_data["columns"]:
                    if len(column) < 2 or len(column) > 3:
                        raise ValueError(
                            "Column did not have two or three "
                            "elements: '%s'" % str(column)
                        )

                    column_name = str(column[0])
                    column_cls = str(column[1])
                    column_desc = str(column[2]) if len(column) > 2 else ""

                    cls = next(
                        (
                            cls
                            for cls_name, cls in column_types
                            if cls_name == column_cls
                        ),
                        None,
                    )
                    if not cls:
                        raise ValueError(
                            "Could not find a column type with name "
                            "'%s' for column '%s'" % (column_cls, column.name)
                        )

                    columns.append(_Column(name=column_name, cls=cls, desc=column_desc))
                datum = SchemeDatum(
                    version=json_data["version"],
                    annotation=json_data["annotation-spec"],
                    extends=else_none(json_data["extends"]),
                    columns=columns,
                    filtered=else_none(json_data["filtered"]),
                )
                data.append(datum)
            except Exception as error:
                raise ValueError(
                    "Could not read from file '%s': %s" % (filename, str(error))
                )
    return data


def scheme_sort_key(scheme):
    """Sort key for sorting schemes.  Sorts by version and then annotation
    spec.  Extracts, major, minor, and patch versions."""

    def extract_version_string(str, which_name):
        """Extracts the version string.  Expects one of the two following
        patterns:
        1. "gdc-[0-9]+\.[0-9]+\.[0-9]"
        2. "gdc-[0-9]+\.[0-9]+\.[0-9]-[a-z]+"
        """
        if not str.startswith("gdc-"):
            return [-1, -1, -1, str]
        gdc_len = len("gdc-")
        str = str[gdc_len:]
        last = ""
        if "-" in str:
            index = str.index("-")
            l_index = index + 1
            last = str[l_index:]
            str = str[:index]
        return list(map(int, str.split("."))) + [last]

    version = extract_version_string(scheme.version(), "version")
    annotation_spec = extract_version_string(scheme.annotation_spec(), "annotation")

    return version + annotation_spec


def load_all_schemes(extra_filenames=None):
    """Load all the built-in schemes and any schemes given with
    ``extra_filename``.  Schemes must have a unique version and annotation
    pair across all schemes."""

    # Get all the known column types
    column_types = get_column_types()

    # Get all the filenames/paths for the scheme jsons
    filenames = get_built_in_filenames()
    if extra_filenames:
        filenames = filenames + extra_filenames

    # Read in all the scheme data, but don't build them yet
    data = load_all_scheme_data(filenames=filenames, column_types=column_types)

    # Build the schemes
    schemes = build_schemes(data=data)

    # Gather all the schemes
    # NB: could sort by version an annotation
    schemes = [NoRestrictionsScheme(column_names=list())] + list(schemes.values())

    # Validate that all schemes have different combinations of version
    # and annotations
    validate_schemes(schemes=schemes)

    # Sort by version
    schemes.sort(key=scheme_sort_key)

    return schemes


__ALL_SCHEMES = []
__LOADED_ALL_SCHEMES = False


def all_schemes(extra_filenames=None):
    """Gets all the known schemes."""
    global __LOADED_ALL_SCHEMES
    global __ALL_SCHEMES
    if not __LOADED_ALL_SCHEMES or extra_filenames:
        __ALL_SCHEMES = load_all_schemes(extra_filenames=extra_filenames)
        __LOADED_ALL_SCHEMES = True
    return __ALL_SCHEMES


def find_scheme_class(version=None, annotation=None):
    """Finds the scheme with the given version and annotation from all the
    known schemes.  If no version is given, get the first scheme with the
    given annotation.  If no annotation is given, find the first scheme with
    both the version and annotation matching the given version (a basic
    scheme).  Returns the class of the scheme."""
    schemes = all_schemes()
    if not version and not annotation:
        raise ValueError("Either version or annotation must be given")
    elif not annotation:
        return next(
            (
                s
                for s in schemes
                if s.version() == version and s.annotation_spec() == version
            ),
            None,
        )
    elif not version:
        return next((s for s in schemes if s.annotation_spec() == annotation), None)
    else:
        return next(
            (
                s
                for s in schemes
                if s.version() == version and s.annotation_spec() == annotation
            ),
            None,
        )


def find_scheme(version=None, annotation=None):
    """Finds the scheme with the given version and annotation from all the
    known schemes.  If no version is given, get the first scheme with the
    given annotation.  If no annotation is given, find the first scheme with
    both the version and annotation matching the given version (a basic
    scheme).  Returns an instance of the scheme."""
    cls = find_scheme_class(version=version, annotation=annotation)
    return cls() if cls else None
