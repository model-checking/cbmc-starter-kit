# AWS Templates for CBMC Proofs

This repository is a "starter kit" for writing CBMC proofs.
[CBMC](https://www.cprover.org/cbmc/)
is a model checker for C code that can prove that the assertions in your code
are never violated and that your code is free
of security vulnerabilites like buffer overflow.  In this starter kit,
* one script ([setup.py](https://github.com/awslabs/aws-templates-for-cbmc-proofs/blob/master/scripts/setup.py))
  installs into your repository a few directories containing code, templates, and Makefiles that will be
  useful for every proof you write, and
* one script ([setup-proof.py](https://github.com/awslabs/aws-templates-for-cbmc-proofs/blob/master/scripts/setup-proof.py))
  installs, for a particular proof, a single directory containing skeletons of all the files you will need
  to write that proof.

The [starter kit wiki](https://github.com/awslabs/aws-templates-for-cbmc-proofs/wiki) is the
primary documentation for the starter kit.  It includes tips on how to plan your proof,
how to write a good proof, and how to debug a failed proof.
It also includes
[installation instructions](https://github.com/awslabs/aws-templates-for-cbmc-proofs/wiki/Installation)
for installing the tools [CBMC](https://github.com/diffblue/cbmc) and
[CBMC viewer](https://github.com/awslabs/aws-viewer-for-cbmc) that you will need to use the starter kit.
You should install these tools now.

What follows is quick start guide to using the starter kit.
It sketchs how to install the starter kit and how to start a new proof.

## Installing the starter kit

If you are working on a new project that does not have the starter kit installed,
you will need to install it from scratch.
If you are working on an existing project that already has the starter kit installed,
you will need to include the starter kit when you clone your project for the first time.

### Using the starter kit on a new project

If the starter kit is not already installed in your project, you must
submodule the starter kit into your project and install it.
To do this, clone your repository as usual, change directory into your
repository, and perform the following steps:

* Choose the path to the source root (eg, /usr/project)
* Choose the path to a directory under the source root that should hold
  the infrastructure (eg, /usr/project/cbmc)
* Submodule the AWS-templates-for-CBMC repository into this directory (eg,
  /usr/project/cbmc/aws-templates-for-cbmc)
  ```
  cd /usr/project/cbmc
  git submodule add https://github.com/awslabs/aws-templates-for-cbmc-proofs.git aws-templates-for-cbmc-proofs
  ```
* Use the script `aws-templates-for-cbmc-proofs/scripts/setup.py` to
  setup the standard directory structure for CBMC proof.
  ```
  cd /usr/project/cbmc
  python3 aws-templates-for-cbmc-proofs/scripts/setup.py
  ```
  The script will ask for the path to the source root `/usr/project`.
  The script will install four directories into `/usr/project/cbmc`:
  * include: contains include files for the proofs
  * sources: contains source code for the proofs
  * stubs: contains stubs for the proofs
  * proofs: contains the proofs themselves (the proof root).

See the [setup wiki page](https://github.com/awslabs/aws-templates-for-cbmc-proofs/wiki/CBMC-starter-kit-setup-script) for more details on how to use the script.

Commit these changes, and you are ready to go.

### Using the starter kit on an existing project

If the starter kit is already installed in your project,
you just have to remember to include the stater kit whenever you clone your repository.
To do this, clone your repository as usual, change directory into your
repository, and run the command:

````
git submodule update --init --checkout --recursive
````

## Starting a new proof

Once the starter kit is installed, you start a new proof by running a
proof setup script.

* Change to a directory under the proof root (/usr/project/cbmc/proofs)
* Run the script `../aws-templates-for-cbmc/scripts/setup-proof.py` and give
  * The name of the function under test.
  * The path to the source file defining the function under test.
  * The path to the source root (eg, /usr/project).

The script will create a directory named for the function, and will
install files needed to run the proof. Now you can cut and paste into
the files, and type `make` to run and debug the proof.
See the
[proof setup wiki page](https://github.com/awslabs/aws-templates-for-cbmc-proofs/wiki/CBMC-starter-kit-setup-proof-script)
for more details on how to use the script and the files it installs.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
