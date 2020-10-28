CBMC Proof Infrastructure
=========================

This directory contains automated proofs of the memory safety of various parts
of the s2n codebase. A continuous integration system validates every
pull request posted to the repository against these proofs, and developers can
also run the proofs on their local machines.

The proofs are checked using the
[C Bounded Model Checker](http://www.cprover.org/cbmc/), an open-source static
analysis tool
([GitHub repository](https://github.com/diffblue/cbmc)). This README describes
how to run the proofs on your local clone of s2n.


Prerequisites
-------------

You will need Python 3 and Exuberant Ctags to generate HTML reports.
On macOS and Linux, you will need Make, plus the CBMC build tools.

* Install python3:
    * On MacOS: `brew install python3`
    * On Ubuntu: `sudo apt-get install python3`
* Install Exuberant Ctags:
    * On MacOS: `brew install ctags`
    * On Ubuntu: `sudo apt-get install ctags`


Installing CBMC
---------------

### MacOS

On MacOS, install CBMC using [Homebrew](https://brew.sh/) with

```sh
brew install cbmc
```

or upgrade (if it's already been installed) with:

```sh
brew upgrade cbmc
```

### Ubuntu

On Ubuntu, install CBMC by downloading the *.deb package from CBMC's [release page](https://github.com/diffblue/cbmc/releases).

Installing CBMC Viewer
----------------------

First, clone the [CBMC Viewer repository](https://github.com/awslabs/aws-viewer-for-cbmc).
Then, install `cbmc-viewer` as an ordinary Python pip package: `sudo make install`.


Running the proofs
------------------

Each of the leaf directories under `proofs` is a proof of the memory safety of a single entry point.
To run a proof, change into the directory for that proof and run `make` on Linux or macOS.
The proofs may take some time to run; they eventually write their output to `cbmc.txt`, which should have the text `VERIFICATION SUCCESSFUL` at the end.


Proof directory structure
-------------------------

This directory contains the following subdirectories:

- `proofs` contains the proofs run against each pull request
- `include` contains the `.h` files needed by proofs
- `source` contains functions useful in multiple CBMC proofs
- `stubs` contains stubs for functions which are modelled by CBMC
