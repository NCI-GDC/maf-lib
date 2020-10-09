"""This module contains an implementation of a disk-backed sorting system.
"""

import abc
import errno
import gzip
import heapq
import os
import struct
import tempfile

from maflib.record import MafRecord
from maflib.sort_order import SortOrder
from maflib.validation import ValidationStringency


class Sorter(object):
    """A class for sorting objects.  Records should be added to the sorter
    with the += or add methods.  When all records have been added, the sorter
    can be iterated over to get the records in sorted order.  The
    implementation requires two things:

    1. An implementation of a SorterCodec than can serialize/encode and
     deserialize/decode objects.
    2. A function that creates an object with total ordering for each object
     being sorted.  The total ordering defines the sort order.
    """

    def __init__(
        self, max_objects_in_ram, codec, key_func, tmp_dir=None, always_spill=True
    ):
        """
        Initializes a sorter object.
        :param max_objects_in_ram:  the maximum # of objects in ram
        :param codec: the codec to encode and decode the object
        :param key_func: a function that creates a key used to determine the
        order of each object
        :param tmp_dir: the optional temporary directory
        :param always_spill: always spill to disk before sorting and
        returning records
        """
        self._max_objects_in_ram = max_objects_in_ram
        self._codec = codec
        self._key_func = key_func
        self._tmp_dir = tmp_dir
        self._stash = [None] * max_objects_in_ram
        self._paths = []
        self._fds = []
        self._objects_in_memory = 0
        self._always_spill = always_spill

    def __iadd__(self, obj):
        """Add an object to be sorted"""
        return self.add(obj)

    def add(self, obj):
        """Add an object to be sorted"""
        key = self._key_func(obj)
        data = self._codec.encode(obj)
        self._stash[self._objects_in_memory] = _SortEntry(key=key, data=data)
        self._objects_in_memory += 1
        if self._objects_in_memory == self._max_objects_in_ram:
            self.__spill()
        return self

    def __iter__(self):
        """:return an iterator over the sorted records"""
        if self._paths or self._always_spill:
            self.__spill()
            m_iter = _MergingIterator(
                paths=self._paths, codec=self._codec, key_func=self._key_func
            )
            for record in m_iter:
                yield record
        else:
            self.__sort_stash()

            def decode(idx):
                """Decodes an entry"""
                entry = self._stash[idx]
                data = entry.data
                return self._codec.decode(data, 0, len(data))

            for i in range(self._objects_in_memory):
                yield decode(i)

    def __sort_stash(self):
        """Sorts the current objects in memory"""
        self._stash[: self._objects_in_memory] = sorted(
            self._stash[: self._objects_in_memory]
        )

    def __spill(self):
        """Spills all the objects to disk"""
        if self._objects_in_memory > 0:
            desc, path = tempfile.mkstemp(".gz", dir=self._tmp_dir)
            # TODO: delete on exit!

            handle = gzip.open(path, "wb")
            self.__sort_stash()
            for i in range(self._objects_in_memory):
                entry = self._stash[i]
                data = entry.data
                handle.write(struct.pack('i', len(data)))
                handle.write(memoryview(data))
                self._stash[i] = None
            handle.close()
            self._paths.append(path)
            self._fds.append(desc)
            self._objects_in_memory = 0

    def close(self):
        """Closes all temporary files."""
        for path, desc in zip(self._paths, self._fds):
            try:
                os.close(desc)
                os.remove(path)
            except OSError as exception:
                if exception.errno != errno.ENOENT:
                    raise exception


class SorterCodec(object):
    """An abstract class for classes that are able to encode an object into
    bytes and decode it from bytes.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def encode(self, obj):
        """Encode the object into an array of bytes"""

    @abc.abstractmethod
    def decode(self, data, start, length):
        """Decode the object from an array of bytes"""


class MafSorterCodec(SorterCodec):
    """Simple codec for encoding and decoding MafRecords"""

    def __init__(
        self,
        column_names=None,
        scheme=None,
        validation_stringency=ValidationStringency.Strict,
    ):
        # NB: if neither column_names nor scheme are given, then encode must be
        # called once before decode, and then the column names from the first
        # record are used.
        self._column_names = column_names
        self._scheme = scheme
        self.validation_stringency = validation_stringency

    def encode(self, record):
        """Encodes a MafRecord"""
        if not self._column_names:
            self._column_names = record.keys()
        return bytearray(source=str(record), encoding='utf-8')

    def decode(self, data, start, length):
        """Decodes the data and re-parses the text, returning a MafRecord"""
        end = start + length
        line = data[start:end].decode('utf-8')
        return MafRecord.from_line(
            line=line,
            column_names=self._column_names,
            scheme=self._scheme,
            validation_stringency=self.validation_stringency,
        )


class MafSorter(Sorter):
    """A sorter for MafRecords"""

    def __init__(
        self,
        sort_order_name,
        scheme=None,
        max_objects_in_ram=10000,
        *so_args,
        **so_kwargs,
    ):
        """
        Construct a sorter for MafRecords
        :param sort_order_name: the canonical name of the sort order
        :param scheme: the scheme to use for the codec
        :param max_objects_in_ram: the maximum number of MafRecords in RAM.
        :param so_args: arguments to the sort order constructor
        :param so_kwargs: keyword arguments to the sort order constructor
        """
        sort_order = SortOrder.find(sort_order_name=sort_order_name)
        sort_order = sort_order(*so_args, **so_kwargs)

        super(MafSorter, self).__init__(
            max_objects_in_ram=max_objects_in_ram,
            codec=MafSorterCodec(scheme=scheme),
            key_func=sort_order.sort_key(),
        )


class _SortEntry(object):
    """A specialized tuple that contains a key used to compare entries, and a
    serialized version of the object being sorted."""

    def __init__(self, key, data):
        """
        :param key: the key used to determine the order of the objects being
        sorted
        :param data: the serialized version of the object being sorted
        """
        self.key = key
        self.data = data

    def __lt__(self, other):
        """
        :param other: the other object of the same type
        :return: true if the current object should come before the other object
        """
        return self.key < other.key


class _SortedIterator(object):
    """An iterator that consumes data from a single tmp file of sorted data and
     produces an iterator of sorted objects. """

    def __init__(self, path, codec, key_func):
        """
        :param path: the path to the tmp file
        :param codec: the codec used to decode
        :param key_func: a function that creates a key used to determine the
        order of each object
        """
        self._path = path
        self._codec = codec
        self._key_func = key_func
        self._handle = gzip.open(path, mode="rb", compresslevel=5)
        self._next_value = None
        self._next_key = None
        self._closed = False
        self.__advance()

    def __advance(self):
        """Gets the next key and value, decoding a record if necessary"""
        if self._closed:
            self.__clear()
        else:
            data = self._handle.read(size=4)
            if data == '' or len(data) == 0:
                self.close()
                self.__clear()
            else:
                length = struct.unpack('i', data)[0]
                data = self._handle.read(size=length)
                self._next_value = self._codec.decode(data, 0, length)
                self._next_key = self._key_func(self._next_value)

    def __lt__(self, other):
        return self.peek_key() < other.peek_key()

    def __iter__(self):
        return self

    def peek_key(self):
        """Gets the next record's key, None if none exists"""
        return self._next_key

    def next(self):
        """Gets the next record in sorted order"""
        return self.__next__()

    def __next__(self):
        if not self._next_value:
            raise StopIteration
        return_value = self._next_value
        self.__advance()
        return return_value

    def __clear(self):
        """Sets the next key and value to None"""
        self._next_value = None
        self._next_key = None

    def close(self):
        """Closes the underlying temporary file"""
        if not self._closed:
            self._handle.close()
            self._closed = True


class _MergingIterator(object):
    """An iterator that merges objects from _SortedIterator and maintains
    ordering"""

    def __init__(self, paths, codec, key_func):
        """
        :param paths: the paths to the tmp files to merge
        :param codec: the codec used to decode
        :param key_func: a function that creates a key used to determine the
        order of each object
        """
        self._heap = []
        self._iterators = []
        for path in paths:
            s_iter = _SortedIterator(path=path, codec=codec, key_func=key_func)
            heapq.heappush(self._heap, s_iter)
            self._iterators.append(s_iter)

    def __iter__(self):
        return self

    def next(self):
        """Gets the next record in sorted order"""
        return self.__next__()

    def __next__(self):
        if not self._heap:
            self.close()
            raise StopIteration
        s_iter = heapq.heappop(self._heap)
        entry = s_iter.next()
        if s_iter.peek_key():
            heapq.heappush(self._heap, s_iter)
        return entry

    def close(self):
        """Closes all the underlying iterators"""
        for s_iter in self._iterators:
            s_iter.close()
        self._iterators = []
        self._heap = []
