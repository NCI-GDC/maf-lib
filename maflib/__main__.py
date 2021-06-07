#!/usr/bin/env python3

try:
    from maflib import __version__
except ImportError:
    __version__ = "0.0.0"


def main() -> None:
    print(__version__)


if __name__ == "__main__":
    main()

# __END__
