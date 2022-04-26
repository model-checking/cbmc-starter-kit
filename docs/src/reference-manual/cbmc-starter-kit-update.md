# Reference manual

## Name

`cbmc-starter-kit-update` - Update CBMC starter kit in a CBMC proof repository

## Synopsis

```
cbmc-starter-kit-update [-h] [--cbmc-root CBMC]
                        [--starter-kit-root STARTER_KIT] [--no-migrate]
                        [--no-test-removal] [--no-update]
                        [--remove-starter-kit-submodule]
                        [--remove-litani-submodule] [--verbose]
                        [--debug] [--version]
```

## Description

This script is used to update the CBMC starter kit installed in your
repository to the lastest version.  It copies (overwrites) two files
into your repository (`Makefile.common` and `run-cbmc-proofs.py`).
These are the two files in the starter kit that encode our best
practices for how to use CBMC in a software verification project.

This script will also migrate your repository from early versions of
the starter kit and litani (the build system used by the starter kit)
to modern versions.  Early versions of the starter kit and litani were
distributed as as git repositories that you submoduled into your
repository.  The starter kit also installed symbolic links from your
repository into the starter kit submodule. This script will remove the
symbolic links (replace them with the files they are linking to) and will
also remove the starter kit and litani submodules from your repository
if you give the `--remove-stater-kit-submodule` and
`--remove-litani-submodule` flags (flags you almost certainly want to
use during the migration).  Finally, it will remove some regression tests
that were distributed with early versions of the starter kit that most people
don't use.

## Options

`--cbmc-root CBMC`

* Root of CBMC proof infrastructure (default: ".")

`--starter-kit-root STARTER_KIT`

* Root of CBMC starter kit submodule (default: None or
  root of starter kit submodule installed in repository
  containing CBMC)

`--no-migrate`

* Do not remove symlinks under CBMC. Normally remove
  symlinks under CBMC to files under STARTER_KIT.

`--no-test-removal`

* Do not remove negative tests in CBMC/negative_tests.
  Normally remove the directory CBMC/negative_tests
  since most projects don't use these tests.

`--no-update`

* Do not update Makefile.common and run-cbmc-proofs.py
  under CBMC/proofs. Normally update these files with
  the versions in the starter kit package.

`--remove-starter-kit-submodule`

* Remove the starter kit submodule if it is present.
  Normally just recommend removal.

`--remove-litani-submodule`

* Remove the litani submodule and update the definition
  of LITANI in Makefile-template-defines if the litani
  submodule is present and the litani command is in
  PATH. Normally just recommend removal.

`--verbose`

* Verbose output

`--debug`

* Debug output

`--version`

* Display version and exit

`--help, -h`

* Print the help message and exit.
