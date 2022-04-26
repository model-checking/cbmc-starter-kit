# Installation

The starter kit is distributed as both a brew package and a pip package, and the
[release page](https://github.com/model-checking/cbmc-starter-kit/releases/latest)
gives installation instructions that we repeat here.

## Brew installation

On MacOS, we recommend using brew to install the starter kit with
```
brew tap aws/tap
brew install cbmc-starter kit
```
and upgrade to the latest version with
```
brew upgrade cbmc-starter kit
```

The [brew home page](https://brew.sh/) gives instructions for installing brew.
The command `brew tap aws/tap` taps the AWS repository that contains the
brew package.

## Pip installation

On any operating system with python installed, use pip to install the
starter kit with
```
python3 -m pip install cbmc-starter-kit
```
and upgrade to the latest version with
```
python3 -m pip install --upgrade cbmc-starter-kit
```

The [python download page](https://www.python.org/downloads/)
gives instructions for installing python and pip.

## Developers

Developers can install the package in "editable mode" which makes
it possible to modify the code in the source tree and then run the command
from the command line as usual to test the changes.
First, optionally install ctags as described above.  Then

* Clone the repository with
  ```
  git clone https://github.com/model-checking/cbmc-starter-kit cbmc-starter-kit
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
  export PATH=$PATH:/tmp/cbmc-starter-kit/bin
  ```

* Uninstall with
  ```
  cd cbmc-starter-kit
  make undevelop
  ```

## Installation notes

If you have difficulty installing these tools, please let us know by
submitting a [GitHub issue](https://github.com/model-checking/cbmc-starter-kit/issues).
