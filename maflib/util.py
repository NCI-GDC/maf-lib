"""A set of useful utility classes and methods"""
import sys
from contextlib import contextmanager
from io import StringIO
from typing import Any, Callable, Generator, Iterator, TextIO, Tuple, Type

from maflib.logger import Logger


class LineReader:
    """
    A little class that can read the next line without consuming it.
    """

    def __init__(self, fh: StringIO):
        self._file = fh
        self._line = self.__read_line()
        self._line_number: int = 0

    def read_line(self) -> str:
        """Reads a single line"""
        cur_line = self._line
        if self._line:
            self._line = self.__read_line()
            self._line_number += 1
        return cur_line

    def __read_line(self) -> str:
        """Reads a line from the underlying file"""
        return self._file.readline().rstrip("\r\n")

    def line_number(self) -> int:
        """
        :return: the number of lines read so far.
        """
        return self._line_number

    def peek_line(self) -> str:
        """Gets the next line without consuming it"""
        return self._line

    def __iter__(self) -> 'LineReader':
        return self

    def next(self) -> str:
        """Gets the next line"""
        return self.__next__()

    def __next__(self) -> str:
        """Gets the next line and consumes it"""
        line = self.peek_line()
        if not line:
            raise StopIteration
        return self.read_line()

    def close(self) -> None:
        """Close the reader and the underling file handle"""
        self._file.close()


TPeekReturn = Any


class PeekableIterator:
    """An iterator that has a `peek()` method."""

    def __init__(self, _iter: Iterator[TPeekReturn]):
        self._iter = _iter
        self.__update_peek()

    def __iter__(self) -> 'PeekableIterator':
        return self

    def next(self) -> TPeekReturn:
        """Gets the next record"""
        return self.__next__()

    def __next__(self) -> TPeekReturn:
        if self._peek is None:
            raise StopIteration
        to_return = self._peek
        self.__update_peek()
        return to_return

    def __update_peek(self) -> None:
        self._peek = next(self._iter, None)

    def peek(self) -> TPeekReturn:
        """Returns the next element without consuming it, or None
        if there are no more elements."""
        return self._peek


@contextmanager
def captured_output() -> Generator[Tuple[TextIO, TextIO], None, None]:
    """Captures stderr and stdout and returns them"""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        Logger.setup_root_logger()
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def extend_class(base_cls: Any, cls: Any) -> Type:
    """Apply mixins"""
    base_cls_name = base_cls.__name__
    return type(base_cls_name, (cls, base_cls), {})


def extend_instance(obj: object, cls: type) -> None:
    """Apply mixins after object creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (cls, base_cls), {})
