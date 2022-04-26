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

Update CBMC starter kit in a CBMC proof repository.

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

`--help, -h`

`--verbose`

* Verbose output

`--debug`

* Debug output

`--version`

* Display version and exit
