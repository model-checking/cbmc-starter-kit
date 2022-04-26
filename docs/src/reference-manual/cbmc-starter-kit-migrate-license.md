# Reference manual

## Name

`cbmc-starter-kit-migrate-license` - Remove references to Apache license from CBMC starter kit.

## Synopsis

```
cbmc-starter-kit-migrate-license [-h] [--proofdir PROOFDIR] [--remove]
                                 [--verbose] [--debug] [--version]
```
## Description

This script is used to remove references to the Apache license installed
by early versions of the starter kit.

The CBMC starter kit was originally released under the Apache
license. All files in the starter kit contained references to the
Apache license. The starter kit installation scripts copied files from
the stater kit into the project repository. This became an issue when
the project repository was released under a more permissive
license. This script removes all references to the Apache license from
the files copied into the project repository from the starter kit, and
uses the MIT-0 license instead.

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
