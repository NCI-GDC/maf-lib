"""Module that contains a class that all subcommands should implement.

* Subcommand  a class that all subcommands of maftools should implement.
"""

from maflib.logger import Logger
from maflib.scheme_factory import all_schemes, find_scheme
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
    def __main__(cls, options):
        """
        The default function when the subcommand is selected.  Returns None if
        executed successfully, or a string message if the options are invalid.
        Should not call __validate_options__ as it will be called elsewhere.
        """

    @classmethod
    def main(cls, options):
        """
        Validates the given options and runs the __main__ method.
        """
        cls.__validate_options__(options)
        return cls.__main__(options)

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
    def __validate_options__(cls, options):
        """
        Validate the custom command line options.  All parsers should
        recursively call this method first, as it will set the "scheme" member
        on the provided options object.
        """
        logger = Logger.get_logger(cls.__name__)

        if options.version or options.annotation:
            options.scheme = find_scheme(version=options.version,
                                         annotation=options.annotation)
            if not options.scheme:
                tuples = ["\t%s %s" % (s.version(), s.annotation_spec()) for
                          s in all_schemes()]
                raise ValueError("Could not find a scheme with version '%s' "
                                 "and annotation '%s'.  Available schemes:\n%s"
                                 % (options.version, options.annotation,
                                    "\n".join(tuples)))
            if options.version is None:
                logger.info(
                    "No version given, defaulting to version '%s' "
                    "based on -a/--annotation",
                    options.scheme.version())
            if options.annotation is None:
                if options.scheme.is_basic():
                    logger.info(
                        "The scheme is assumed to be the basic scheme")
                else:
                    logger.info("No annotation given, defaulting to "
                                "annotation '%s'",
                                options.scheme.annotation_spec())
        else:
            options.scheme = None

    @classmethod
    def add(cls, subparsers):
        """Adds the given subcommand to the subparsers.  Will always add the
        version and annotation options."""
        subparser = subparsers.add_parser(
            name=cls.__get_name__(),
            description=cls.__get_description__())

        versions = list(set(s.version() for s in all_schemes()))
        annotations = [s.annotation_spec() for s in all_schemes()]

        subparser.add_argument('-v', '--version',
                               default=None,
                               choices=versions,
                               help="Use the given version when validating "
                                    "rather than what's in the header.  "
                                    "Choices: %s" % ", ".join(versions))
        subparser.add_argument('-a', '--annotation',
                               type=str, default=None,
                               choices=annotations,
                               help="Use the given annotation specification "
                                    "when validating rather than what's in "
                                    "the header.  "
                                    "Choices: %s" % ", ".join(annotations))

        cls.__add_arguments__(subparser)
        subparser.set_defaults(func=cls.main)
        return subparser
