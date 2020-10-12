#!/usr/bin/env python3

try:
    from maflib._version import __pypi_version__

    __version__ = __pypi_version__
except ImportError:
    __version__ = "0.0.0"

if __name__ == "__main__":
    print(__version__)

# __END__
