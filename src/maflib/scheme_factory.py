"""Module for building schemes"""

import glob
import json
import os
import re
from collections import OrderedDict, namedtuple

from maflib.column_types import get_column_types
from maflib.schemes import MafScheme, NoRestrictionsScheme
from maflib.util import extend_class

SchemeDatum = namedtuple("SchemeDatum", ["version",
                                         "annotation",
                                         "extends",
                                         "columns",
                                         "filtered"])


def combine_column_dicts(base_dict,
                         extra_dict=None,
                         filtered=None):
    """ Combines columns when building a scheme.

    The `base_dict` and `extra_dict` should be ordered dictionaries from
    column name (`str`) to the class for the column type.

    Any columns in `extra_dict` that are also in `base_dict` will have the
    column type from `extra_dict` mixed into `base_dict`.  New columns from
    `extra_dict` will be appended.

    `filtered_column_name_set` can be used to _remove_ any columns from
    either the `base_dict` or the `extra_dict` after they are combined.
    """
    column_dict = OrderedDict(base_dict)

    if extra_dict:
        # add any additional types to the base columns
        for column_name in extra_dict:
            if column_name in column_dict:
                column_dict[column_name] = \
                    extend_class(column_dict[column_name],
                                 extra_dict[column_name])

        # add the extra_columns
        column_dict.update([(k, v) for k, v in extra_dict.items()
                            if k not in column_dict])

    if filtered is not None:
        new_columns = OrderedDict()
        for k, value in column_dict.items():
            if k not in filtered:
                new_columns[k] = value
        column_dict = new_columns
        # TODO: detect if somethign in filtered was not present in the dict

    return column_dict


def build_scheme_class(datum, base_scheme, column_types):
    """
    :param datum: a scheme datum class
    :param base_scheme: the base scheme, or None if no base scheme
    :param column_types: a tuple of (name, class) for all known column types
    :return: a new MafScheme
    """

    # create a column_dictionary
    column_dict = OrderedDict()
    if datum.columns:
        for column_name, column_cls_name in datum.columns:
            cls = next((cls for cls_name, cls in column_types
                        if cls_name == column_cls_name), None)
            if not cls:
                raise ValueError("Could not find a column type with name "
                                 "'%s' for column '%s'" \
                                 % (column_cls_name,
                                    column_name))
            column_dict[str(column_name)] = cls

    # extend the base scheme if necessary
    if base_scheme:
        column_dict = combine_column_dicts(
            base_dict=base_scheme.__column_dict__(),
            extra_dict=column_dict,
            filtered=datum.filtered
        )

    name = "_".join([x.capitalize()
                     for x in re.split(r"[-.]", datum.annotation)])

    # now create the scheme
    tpe = type(str(name), (MafScheme,), {})
    setattr(tpe, "version", classmethod(lambda cls: datum.version))
    setattr(tpe, "annotation_spec", classmethod(lambda cls: datum.annotation))
    setattr(tpe, "__column_dict__", classmethod(lambda cls: column_dict))

    #return type(str(name), (MafScheme,), {
    #    "version": lambda(cls): datum.version,
    #    "annotation_spec": lambda(cls): datum.annotation,
    #    "__column_dict__": lambda(cls): column_dict
    #})

    return tpe


def build_schemes(data, column_types):
    """
    Builds the schemes represented by the list of ``SchemeDatum``s.
    :return: a mapping from the scheme annotation to the scheme
    """
    schemes = {}  # annotation -> scheme
    while data:
        # find a scheme data that either doesn't extend any other scheme, or
        # whose base scheme it extends we have already built
        datum_index, datum = next(
            ((i, d) for (i, d) in enumerate(data) if not d.extends or
             d.extends in schemes), (None, None))
        if not datum:
            annotations = ", ".join([d.annotation for d in data])
            raise ValueError("Could not find a scheme to build.  Schemes "
                             "remaining annotations were: %s" % annotations)
        scheme_cls = build_scheme_class(datum=datum,
                                        base_scheme=schemes.get(datum.extends),
                                        column_types=column_types)
        schemes[scheme_cls.annotation_spec()] = scheme_cls
        del data[datum_index]
    return schemes


def validate_schemes(schemes):
    """Validate that all schemes have different combinations of version
    and annotations
    """
    schemes = list(schemes)
    num_schemes = len(schemes)
    for i in range(num_schemes-1):
        left = schemes[i]
        for j in range(i+1, num_schemes):
            right = schemes[j]
            if left.version() == right.version() \
                    and left.annotation_spec() == right.annotation_spec():
                raise ValueError("Two schemes found with version '%s' and "
                                 "annotation specification '%s'" % (
                                     str(left.version()),
                                     str(left.annotation_spec())))

    return True


def get_built_in_filenames(filename=None):
    """
    Gets all the scheme filenames for built in schemes.
    """
    if not filename:
        filename = __file__
    path = os.path.join(os.path.dirname(filename), "resources")
    return glob.glob(os.path.join(path, "*json"))


def load_all_scheme_data(filenames):
    """
    Load all the scheme data from the json file names
    :param filenames: a list of filenames for the json schemes
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
                columns = [(str(column[0]), str(column[1]))
                           for column in json_data["columns"]]
                datum = SchemeDatum(
                    version=json_data["version"],
                    annotation=json_data["annotation-spec"],
                    extends=else_none(json_data["extends"]),
                    columns=columns,
                    filtered=else_none(json_data["filtered"])
                )
                data.append(datum)
            except Exception as error:
                raise ValueError("Could not read from file '%s': %s"
                                 % (filename, str(error)))
    return data


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
    data = load_all_scheme_data(filenames=filenames)

    # Build the schemes
    schemes = build_schemes(data=data, column_types=column_types)

    # Gather all the schemes
    # NB: could sort by version an annotation
    schemes = [NoRestrictionsScheme(column_names=list())] \
              + list(schemes.values())

    # Validate that all schemes have different combinations of version
    # and annotations
    validate_schemes(schemes=schemes)

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
        return next((s for s in schemes if s.version() == version and
                     s.annotation_spec() == version), None)
    elif not version:
        return next((s for s in schemes if s.annotation_spec() == annotation),
                    None)
    else:
        return next((s for s in schemes if s.version() == version and
                     s.annotation_spec() == annotation), None)

def find_scheme(version=None, annotation=None):
    """Finds the scheme with the given version and annotation from all the
    known schemes.  If no version is given, get the first scheme with the
    given annotation.  If no annotation is given, find the first scheme with
    both the version and annotation matching the given version (a basic
    scheme).  Returns an instance of the scheme."""
    cls = find_scheme_class(version=version, annotation=annotation)
    return cls() if cls else None

