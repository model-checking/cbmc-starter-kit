# Reference manual

## Name

`cbmc-starter-kit-setup-proof` - Set up CBMC proof infrastructure for a proof

## Synopsis

```
cbmc-starter-kit-setup-proof [-h] [--verbose] [--debug] [--version]
```

## Description

This script sets up the CBMC proof infrastructure for an individual proof.
It asks for the name of the function under test.
It then searches the repository for source files that define a
function with that name, and asks you to select the file giving the
implementation you want to test.
If none of the files listed is the correct file, you can give the path
to the correct source file yourself.
Finally, the script creates a directory with the name of the function
and copies into that directory some files to simplify getting started
with the verification of that function.  Most important, it copies
a skeleton of a Makefile and skeleton of a proof harness that you can
edit to get started.

This script is usually run in the CBMC verification root
(the directory you created to hold the CBMC verification work,
and in which you ran the `cbmc-stater-kit-setup` script).
This script can, however, be run in any subdirectory of the
CBMC verification root.  In this way, you can group verification of
similar functions together in a hierarchy of subdirectories.

This script will need to be run once for each function you want
to verify.

## Options

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.

`--help, -h`

* Print the help message and exit.
