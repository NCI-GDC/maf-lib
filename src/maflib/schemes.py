"""A module containing schemes for a MAF file.  A scheme determines the
number of columns, their names, and their expected values.  A scheme can be
determined from the version and annotation specification in the MAF header's
version and annotation specification pragmas respectively.

* MafScheme                  the base scheme all schemes should implement
* NoRestrictionsScheme       a scheme that has no restrictions on the column
                             names and values.
* GdcV1_0_0_BasicScheme      the GDC v1.0.0 basic scheme
* GdcV1_0_0_PublicScheme     the GDC v1.0.0 public scheme
* GdcV1_0_0_ProtectedScheme  the GDC v1.0.0 protected scheme
"""
import abc
from collections import OrderedDict

from maflib.column import MafColumnRecord
from maflib.util import abstractclassmethod


class MafScheme(object):
    """ The base scheme all schemes should implement.

    Sub-classes should implement ``version()``, ``annotation``, and
    ``__column_dict__()``.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, column_dict=None):
        """Create a new MafScheme.  If a ``column_dict`` is supplied,
        use that one, otherwise, use the one from ``__column_dict__``."""
        self.__column_dict = self.__column_dict__() \
            if column_dict is None else column_dict
        self.__column_name_to_column_class = \
            OrderedDict((name, cls) for name, cls in self.__column_dict.items())
        self.__column_name_to_column_index = \
            OrderedDict((name, i) for i, (name, _) in
                        enumerate(self.__column_dict.items()))

    def column_class(self, name):
        """Get the class for the column with the given name"""
        return self.__column_name_to_column_class.get(name, None)

    def column_index(self, name):
        """Get the zero-based index for the column with the given name"""
        return self.__column_name_to_column_index.get(name, None)

    def column_names(self):
        """Get names of the columns in order of column index"""
        return list(self.__column_name_to_column_class.keys())

    @classmethod
    def is_basic(cls):
        """Returns true if the scheme is a "basic" scheme, false otherwise."""
        version = cls.version()
        annotation = cls.annotation_spec()
        if version is not None and annotation is not None:
            return cls.version() == cls.annotation_spec()
        else:
            return False

    @classmethod
    @abstractclassmethod
    def version(cls):
        """
        :return: the canonical version string
        """

    @classmethod
    @abc.abstractmethod
    def annotation_spec(cls):
        """
        :return: the annotation specification
        """

    @classmethod
    @abstractclassmethod
    def __column_dict__(cls):
        """
        :return: A mapping between column name and class for the column type.
        """

    def __str__(self):
        return self.version()

    def __len__(self):
        """
        :return: The number of columns in this scheme
        """
        return len(self.__column_name_to_column_class)


class NoRestrictionsScheme(MafScheme):
    """A MafScheme with no restrictions on the column names and values.  A
    list of column names should be ge given when constructed."""

    def __init__(self, column_names):
        column_dict = OrderedDict((name, MafColumnRecord)
                                  for name in column_names)
        super(NoRestrictionsScheme, self).__init__(column_dict=column_dict)

    @classmethod
    def version(cls):
        return "no-version"

    @classmethod
    def annotation_spec(cls):
        return "no-annotation-specification"

    @classmethod
    def __column_dict__(cls):
        raise ValueError("__column_dict__ may not be called on "
                         "NoRestrictionsScheme")
