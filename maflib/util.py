"""A set of useful utility classes and methods"""
import sys
from contextlib import contextmanager

from maflib.logger import Logger

try:
    # Python 2
    from cStringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO


class LineReader(object):
    """
    A little class that can read the next line without consuming it.
    """

    def __init__(self, fh):
        self._file = fh
        self._line = self.__read_line()
        self._line_number = 0

    def read_line(self):
        """Reads a single line"""
        cur_line = self._line
        if self._line:
            self._line = self.__read_line()
            self._line_number += 1
        return cur_line

    def __read_line(self):
        """Reads a line from the underlying file"""
        return self._file.readline().rstrip("\r\n")

    def line_number(self):
        """
        :return: the number of lines read so far.
        """
        return self._line_number

    def peek_line(self):
        """Gets the next line without consuming it"""
        return self._line

    def __iter__(self):
        return self

    def next(self):
        """Gets the next line"""
        return self.__next__()

    def __next__(self):
        """Gets the next line and consumes it"""
        line = self.peek_line()
        if not line:
            raise StopIteration
        return self.read_line()

    def close(self):
        """Close the reader and the underling file handle"""
        self._file.close()


class PeekableIterator(object):
    """An iterator that has a `peek()` method."""

    def __init__(self, _iter):
        self._iter = _iter
        self.__update_peek()

    def __iter__(self):
        return self

    def next(self):
        """Gets the next record"""
        return self.__next__()

    def __next__(self):
        if self._peek is None:
            raise StopIteration
        to_return = self._peek
        self.__update_peek()
        return to_return

    def __update_peek(self):
        self._peek = next(self._iter, None)

    def peek(self):
        """Returns the next element without consuming it, or None
        if there are no more elements."""
        return self._peek


class abstractclassmethod(classmethod):
    """A class that can be used to annotate an abstract class method"""

    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


@contextmanager
def captured_output():
    """Captures stderr and stdout and returns them"""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        Logger.setup_root_logger()
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def extend_class(base_cls, cls):
    """Apply mixins"""
    base_cls_name = base_cls.__name__
    return type(base_cls_name, (cls, base_cls), {})


def extend_instance(obj, cls):
    """Apply mixins after object creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (cls, base_cls), {})
