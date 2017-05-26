"""Module that contains a class that all subcommands should implement.

* Subcommand  a class that all subcommands of maftools should implement.
"""
from maflib.util import abstractclassmethod


class Subcommand(object):
    """A class that all maftool subcommands should implement"""
    @classmethod
    @abstractclassmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """

    @classmethod
    @abstractclassmethod
    def main(cls, options):
        """
        The default function when the subcommand is selected.  Returns None if
        executed successfully, or a string message if the options are invalid. 
        """

    @classmethod
    def __get_name__(cls):
        """
        Gets the name to use for the sub-parser
        """
        return cls.__name__.lower()

    @classmethod
    def __get_title__(cls):
        """
        Gets the title to use for the sub-parser
        """
        return cls.__name__.lower()

    @classmethod
    def __get_description__(cls):
        """
        Gets the description to use for the sub-parser
        """
        return None

    @classmethod
    def add(cls, subparsers):
        """Adds the given subcommand to the subparsers"""
        subparser = subparsers.add_parser(name=cls.__get_name__(),
                                          description=cls.__get_description__())
        cls.__add_arguments__(subparser)
        subparser.set_defaults(func=cls.main)
        return subparser
