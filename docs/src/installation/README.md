# Installation

The starter kit is a command line tool distributed as both a brew package and a pip package.
The [starter kit release page](https://github.com/model-checking/cbmc-starter-kit/releases/latest)
gives installation instructions that we repeat here.

Note: The starter kit used to be distributed as a git repository that you submoduled into
your own repository.  The starter kit is now distributed as a command line tool.  Follow
the [update instructions](#updating-to-the-command-line-tool) below to upgrade your project
from using the submodule to using the command line tool.

## Installing with brew

On MacOS, we recommend using brew to install the starter kit:
```
brew tap aws/tap
brew install cbmc-starter-kit cbmc-viewer litani
```

The [brew home page](https://brew.sh/) gives instructions for installing brew.
The command `brew tap aws/tap` taps the AWS repository that contains the brew packages.
The [cbmc-viewer](https://github.com/model-checking/cbmc-viewer)
and [litani](https://github.com/awslabs/aws-build-accumulator) packages are tools
used by the starter kit.
See the [cbmc-viewer release page](https://github.com/model-checking/cbmc-viewer/releases/latest)
and the [litani release page](https://github.com/awslabs/aws-build-accumulator/releases/latest)
for other ways to install them if you don't want to use brew.

## Installing with pip

On any machine, you can use pip to install the starter kit:
```
python3 -m pip install cbmc-starter-kit cbmc-viewer
```

The [python download page](https://www.python.org/downloads/)
gives instructions for installing python and pip.
The [cbmc-viewer](https://github.com/model-checking/cbmc-viewer)
and [litani](https://github.com/awslabs/aws-build-accumulator) packages are tools
used by the starter kit.
See the [cbmc-viewer release page](https://github.com/model-checking/cbmc-viewer/releases/latest)
and the [litani release page](https://github.com/awslabs/aws-build-accumulator/releases/latest)
for installation instructions (we used pip to install `cbmc-viewer` in the command above).

## Installing for developers

Developers can install the package in "editable mode" which makes
it possible to modify the code in the source tree and then run the command
from the command line as usual to test the changes.
First, install `cbmc-viewer` and `litani` as described above if you haven't already.
Then

* Clone the repository and install dependencies with
  ```
  git clone https://github.com/model-checking/cbmc-starter-kit cbmc-starter-kit
  python3 -m pip install virtualenv gitpython
  ```
* Install into a virtual environment with
  ```
  cd cbmc-starter-kit
  make develop
  ```
  At this point you can either activate the virtual environment with
  ```
  source /tmp/cbmc-starter-kit/bin/activate
  ```
  or simply add the virtual environment to your path with
  ```
  export PATH=/tmp/cbmc-starter-kit/bin:$PATH
  ```

* Uninstall with
  ```
  cd cbmc-starter-kit
  make undevelop
  ```
## Updating

To update to the the latest version of the starter kit:
* Update the starter kit itself with
  ```
  brew upgrade cbmc-starter-kit
  ```
  or
  ```
  python3 -m pip install cbmc-starter-kit --upgrade
  ```
* Update your repository by changing to the `cbmc` directory that contains the `proofs`
  directory installed by the starter kit and running the update script:
  ```
  cd cbmc
  cbmc-starter-kit-update
  ```
  This will overwrite `Makefile.common` and `run-cbmc-proofs.py` in the `proofs` directory
  with the latest versions.

## Updating to the command line tool

The starter kit used to be distributed as a git repository that you submoduled into your
own repository.  The same used to be true for litani, the build tool used by the starter kit.
Now both are distributed a command line tools.
We recommend that you migrate to using these command line tools.

* Install the starter kit and litani as command line tools
  * On MacOS
    ```
    brew install cbmc-starter-kit litani
    ```
  * On Ubuntu, first download the litani debian package from the
    [litani release page](https://github.com/awslabs/aws-build-accumulator/releases/latest) then
    ```
    python3 -m pip install cbmc-starter-kit
    apt install ./litani-*.deb
    ```
* Change to the `cbmc` directory that contains the `proofs` directory installed by the
  starter kit, and run the update script
  ```
  cd cbmc
  cbmc-starter-kit-update --remove-starter-kit-submodule --remove-litani-submodule
  ```
  This will overwrite `Makefile.common` and `run-cbmc-proofs.py` in the `proofs` directory
  with the latest versions, and remove the submodules for the starter kit and litani
  if they are present.  It will also perform some cleanup actions, such as replacing symbolic
  links into the starter kit submodule with copies of the files being linked to, and removing
  a set of negative tests that are rarely used.

  See [cbmc-starter-kit-update](../reference-manual/cbmc-starter-kit-update.md)
  for more information.

While you are at it, we have changed the starter kit license from Apache 2.0 to MIT-0, and
you might want to run a script to change copyright headers from Apache to MIT in files
under the `cbmc` directory:
```
cd cbmc
cbmc-starter-kit-migrate-license --remove
```
See [cbmc-starter-kit-migrate-license](../reference-manual/cbmc-starter-kit-migrate-license.md)
for more information.

## Running CBMC proofs as part of CI

The starter kit offers GitHub repositories with the ability to run CBMC proofs
in GitHub Actions. If the proofs are unable to run in
[GitHub's standard Runner](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#supported-runners-and-hardware-resources),
you may need to constrain some proofs' parallelism with the
[`EXPENSIVE`](https://model-checking.github.io/cbmc-starter-kit/tutorial/index.html#the-makefile)
setting, or [create a Large Runner for your repository](https://docs.github.com/en/actions/using-github-hosted-runners/using-larger-runners).

See [cbmc-starter-kit-setup-ci](../reference-manual/cbmc-starter-kit-setup-ci.md)
for more information.

## Installation notes

If you have difficulty installing these tools, please let us know by
submitting a [GitHub issue](https://github.com/model-checking/cbmc-starter-kit/issues).
