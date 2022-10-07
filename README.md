![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/NCI-GDC/maf-lib)
[![Language](https://img.shields.io/badge/language-python-brightgreen.svg)](http://www.python.org/)
![GitHub branch checks state](https://img.shields.io/github/checks-status/NCI-GDC/maf-lib/main)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)

# MAF-LIB: the Mutation Annotation Format Library

Python API library and command line tools for GDC MAF files.

<!---toc start-->
  * [Contributing](#contributing)
  * [Installation](#installation)
  * [API](#api)

<!---toc end-->

## Contributing

Read how to contribute [here](CONTRIBUTING.md).

## Installation

To install: `pip install git+https://github.com/NCI-GDC/maf-lib.git@2.3.3`.

## API

The MAF API can be found in `maflib/`.
Documentation can be generated using your favorite python documentation
tool, such as `pydoc`.

The library includes but is not limited to the following modules:

| Module | Description |
| --- | --- |
| `maflib.reader` | a module for reading MAF file |
| `maflib.writer` | a module for writing MAF files |
| `maflib.header` | a module for data stored in a MAF header, including but not limited to the version, annotation specification, sort order, and column names |
| `maflib.record` | a module to store a single line of the MAF file, or more specifically, the annotation values for a single mutation |
| `maflib.column` | a module to store a possibly typed column value for a MAF record |
| `maflib.column_types` | a module containing custom types for columns in a MAF file |
| `maflib.column_values` | a module containing custom enumeration values for columns in a MAF file |
| `maflib.schemes` | a module containing the schemes for a MAF file, determining the number of columns, their names, and their expected values |
| `maflib.sort_order` | a module containing the available sort orders to order records in a MAF file. |
| `maflib.sorter` | a module containing an implementation of a disk-backed sorting system. |
| `maflib.validation` | a module for the underlying validation of values stored in MAF files. |
| `maflib.overlap_iter` | a module containing an implementation of an iterator over MAF records that overlap across multiple MAF files. |
| `maflib.locatable` | a module containing interfaces for "locatable" MAF records, namely those that have a genomic span |

The GDC has specific "schemes" that determine the number of columns, their names, and their expected values.
Pre-defined schemes can be found in the `src/maflib/resources` directory.
The following schemes are natively supported:

| Scheme Name | Type | Inherits From |
| --- | --- | --- |
| gdc.1.0.0 | Basic | None |
| gdc.1.0.0-protected | Protected | gdc.1.0.0  |
| gdc.1.0.0-public | Public | gdc.1.0.0-protected |
| gdc.1.0.1-protected | Protected | gdc.1.0.0  |
| gdc.1.0.1-public | Public | gdc.1.0.1-protected |
