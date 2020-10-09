import os
import unittest

from maflib.tests.testutils import tmp_file
from maflib.util import *


class TestLineReader(unittest.TestCase):

    def test_empty_file(self):
        fh, fn = tmp_file(lines=[])
        reader = LineReader(fh=fh)
        self.assertEqual(reader.peek_line(), "")
        self.assertEqual(reader.read_line(), "")
        self.assertEqual(reader.line_number(), 0)
        reader.close()
        os.remove(fn)

    def test_single_line(self):
        line = "A single line"
        fh, fn = tmp_file(lines=[line])
        reader = LineReader(fh=fh)
        self.assertEqual(reader.line_number(), 0)
        self.assertEqual(reader.peek_line(), line)
        self.assertEqual(reader.read_line(), line)
        self.assertEqual(reader.line_number(), 1)
        self.assertEqual(reader.peek_line(), "")
        self.assertEqual(reader.read_line(), "")
        self.assertEqual(reader.line_number(), 1)
        reader.close()
        os.remove(fn)

    def test_multiple_line(self):
        lines = ["A few", "good", "lines"]
        fh, fn = tmp_file(lines=lines)
        reader = LineReader(fh=fh)
        num_lines = 0
        for i, line in enumerate(reader):
            line_number = i + 1
            self.assertEqual(line, lines[i])
            self.assertEqual(line_number, reader.line_number())
            if line_number < len(lines):
                self.assertEqual(reader.peek_line(), lines[i+1])
            num_lines += 1
        self.assertEqual(num_lines, len(lines))
        reader.close()
        os.remove(fn)


class TestPeekableIterator(unittest.TestCase):

    def test_simple_iteration(self):
        items = [i for i in range(10)]
        self.assertListEqual(
            items,
            [item for item in PeekableIterator(iter(items))]
        )

    def test_peek(self):
        items = PeekableIterator(iter([i for i in range(10)]))

        for i, item in enumerate(items):
            if i == 9:
                self.assertEqual(items.peek(), None)
            else:
                self.assertEqual(items.peek(), i+1)


class TestMisc(unittest.TestCase):
    class Hello(object):
        def __str__(self):
            return "hello"

    class World(object):
        def __str__(self):
            return "world"

    def test_extend_class(self):
        base_cls = TestMisc.Hello
        cls = extend_class(base_cls, TestMisc.World)
        self.assertEqual(str(base_cls()), "hello")
        self.assertEqual(str(cls()), "world")

    def test_extend_instance(self):
        base_cls = TestMisc.Hello
        obj = base_cls()
        self.assertEqual(str(obj), "hello")
        extend_instance(obj, TestMisc.World)
        self.assertEqual(str(obj), "world")
