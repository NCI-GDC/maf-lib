"""Module for maftools parsing utilities"""
import argparse
import sys

from maflib.header import MafHeader
from maflib.writer import MafWriter


class EnumType(object):
    """
    Factory for creating enum object types
    See: https://bugs.python.org/issue25061
    """
    def __init__(self, enumclass, action):
        self.enums = enumclass
        self.action = action

    def __call__(self, astring):
        name = self.enums.__name__
        try:
            value = self.enums[astring]
        except KeyError:
            msg = ', '.join([t.name for t in self.enums])
            msg = '%s: use one of {%s}' % (name, msg)
            raise argparse.ArgumentTypeError(msg)
        else:
            # ugly hack to prevent post validation from choices
            self.action.choices = None
            return value

    def __repr__(self):
        astr = ', '.join([t.name for t in self.enums])
        return '%s(%s)' % (self.enums.__name__, astr)


class StoreEnumAction(argparse._StoreAction):
    """
    See: https://bugs.python.org/issue25061
    """
    def __init__(self,
                 option_strings,
                 dest,
                 type,
                 nargs=None,
                 const=None,
                 default=None,
                 required=False,
                 help=None,
                 metavar=None):
        choices = tuple(t.name for t in type)
        super(StoreEnumAction, self).__init__(option_strings=option_strings,
                                              dest=dest,
                                              nargs=nargs,
                                              const=const,
                                              default=default,
                                              type=EnumType(type, self),
                                              choices=choices,
                                              required=required,
                                              help=help,
                                              metavar=metavar)


def writer_from_reader(reader, options):
    """
    Builds a writer from the given reader and command line options.
    :param options: the command line options, which should have "output",
    "version", and "annotation" defined.
    :param reader: the reader from which to records will be obtained
    :return:
    """
    out_header = MafHeader.from_reader(
        reader=reader,
        version=options.version,
        annotation=options.annotation,
        sort_order=options.sort_order \
            if hasattr(options, 'sort_order') else None
    )

    if options.output:
        writer = MafWriter.from_path(
            path=options.output,
            header=out_header,
            validation_stringency=options.validation_stringency
        )
    else:
        writer = MafWriter.from_fd(
            desc=sys.stdout,
            header=out_header,
            validation_stringency=options.validation_stringency
        )
    return writer
