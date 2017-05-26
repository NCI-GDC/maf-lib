import unittest

from maftools.subcommand import Subcommand


class TestSubcommand(unittest.TestCase):
    class Example(Subcommand):
        @classmethod
        def __add_arguments__(cls, subparser):
            pass

        @classmethod
        def main(cls, options):
            pass

    def test_get_title(self):
        self.assertEqual(TestSubcommand.Example.__get_title__(), "example")
        self.assertEqual(TestSubcommand.Example.__get_name__(), "example")

        self.assertEqual(Subcommand.__get_title__(), "subcommand")
        self.assertEqual(Subcommand.__get_name__(), "subcommand")

    def test_get_description(self):
        self.assertIsNone(Subcommand.__get_description__())
