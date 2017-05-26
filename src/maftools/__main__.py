"""A module for the main method for maftools"""
import argparse
from signal import signal, SIGPIPE, SIG_DFL

from maflib.logger import Logger
from maflib.scheme_factory import all_schemes
from maflib.validation import ValidationStringency
from maftools.sort import Sort
from maftools.util import StoreEnumAction
from maftools.validate import Validate
from maftools.view import View

signal(SIGPIPE, SIG_DFL)


def main(args=None, extra_subparser=None):
    """The main method for maf tools"""
    Logger.setup_root_logger()

    parser = argparse.ArgumentParser()

    # Add any pre-subcommand arguments
    parser.add_argument('-v', '--validation-stringency',
                        action=StoreEnumAction,
                        type=ValidationStringency,
                        default=ValidationStringency.Strict)
    # Add any pre-subcommand arguments
    parser.add_argument('-s', '--schemes', action='append',
                        help="One or more JSON files with custom scheme "
                             "definitions")

    # Add subparsers here
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True
    Validate.add(subparsers=subparsers)
    View.add(subparsers=subparsers)
    Sort.add(subparsers=subparsers)
    if extra_subparser:
        extra_subparser.add(subparsers=subparsers)

    options = parser.parse_args(args=args)

    # Add any custom schemes to the set of known schemes
    all_schemes(extra_filenames=options.schemes)

    options.func(options)

if __name__ == '__main__':
    main()
