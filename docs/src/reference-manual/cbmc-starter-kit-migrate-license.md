# Reference manual

## Name

`cbmc-starter-kit-migrate-license` - Remove references to Apache license from CBMC starter kit.

## Synopsis

```
cbmc-starter-kit-migrate-license [-h] [--proofdir PROOFDIR] [--remove]
                                 [--verbose] [--debug] [--version]
```
## Description

Remove references to Apache license from CBMC starter kit.

The CBMC starter kit was originally released under the Apache license. All
files in the starter kit contained references to the Apache license. The
starter kit installation scripts copied files from the stater kit into the
project repository. This became an issue when the project repository was
released under a different license. This script removes all references to the
Apache license from the files copied into the project repository from the
starter kit.

## Options

`--proofdir PROOFDIR`

* Root of the proof subtree (default: .)

`--remove`

* Remove Apache references from files under PROOFDIR (otherwise just list them)

`--help, -h`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
