# MAF-LIB: the Mutation Annotation Format Library

Python API library and command line tools for GDC MAF files.

<!---toc start-->
  * [Contributing](#contributing)
  * [Building](#building)
  * [API](#api)
  * [Tools](#tools)

<!---toc end-->

## Contributing

Read how to contribute [here](https://github.com/NCI-GDC/gdcapi/blob/master/CONTRIBUTING.md).

## Building

To clone the repository: `git clone git@github.com:NCI-GDC/maf-lib.git`.

To install locally: `python setup.py install`.

## API

The MAF API can be found in `src/maflib`.
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

## Tools

The source for a set of command line tools for manipulating MAF files can be found in `src/maftools`.
Once installed, they can be invoked via `maftools <global options> <tool name>
 <tool options>`, for example `maftools -v Strict view -i in.maf`.
Use the `-h` option with any tool to see command line help.

Support tools are as follows:

| Tool | Description |
| --- | --- |
| `sort` | Sort a MAF file |
| `validate` | Validate the format of a MAF file |
| `view` | View a MAF file |
