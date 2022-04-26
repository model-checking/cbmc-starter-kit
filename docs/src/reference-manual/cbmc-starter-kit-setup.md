# Reference manual

## Name

`cbmc-starter-kit-setup` - Set up CBMC proof infrastructure for a repository

## Synopsis

```
cbmc-starter-kit-setup [-h] [--verbose] [--debug] [--version]
```

## Description

This script sets up the CBMC proof infrastructure for a repository.
It locates the root of the repository, it asks for a name to use
for the CBMC verification activity (any name will do, and the name can be
changed at any time), and it copies into the current directory a collection
of files that simplify getting started with CBMC.

We recommend that you create a directory with a name like `cbmc` somewhere
within the repository to hold the CBMC verification work.  This script
assumes that it is running in this verification directory, and assumes
that this directory is under the root of a git repository.

This script needs to be run only one time to prepare the repository for
CBMC verification.

## Options

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.

`--help, -h`

* Print the help message and exit.
