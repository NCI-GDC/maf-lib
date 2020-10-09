import unittest

from maflib.util import captured_output
from maftools.__main__ import main
from maftools.subcommand import Subcommand


class TestSubcommand(unittest.TestCase):
    class Example(Subcommand):
        @classmethod
        def __add_arguments__(cls, subparser):
            pass

        @classmethod
        def __main__(cls, options):
            pass

    def test_get_title(self):
        self.assertEqual(TestSubcommand.Example.__get_title__(), "example")
        self.assertEqual(TestSubcommand.Example.__get_name__(), "example")

        self.assertEqual(Subcommand.__get_title__(), "subcommand")
        self.assertEqual(Subcommand.__get_name__(), "subcommand")

    def test_get_description(self):
        self.assertIsNone(Subcommand.__get_description__())

    def test_no_inputs(self):
        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit) as context:
                main(args=['example'])

    def test_unknown_scheme(self):
        scheme = "not-a-scheme"
        with self.assertRaises(SystemExit):
            with captured_output():
                main(args=['example', '--version', scheme],
                     extra_subparser=TestSubcommand.Example)
