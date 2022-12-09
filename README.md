# CBMC starter kit

This is a starter kit for writing CBMC proofs.

[CBMC](https://github.com/diffblue/cbmc) is a model checker for
C. This means that CBMC will explore all possible paths through your code
on all possible inputs, and will check that all assertions in your code are
true.
CBMC can also check for the possibility of
memory safety errors (like buffer overflow) and for instances of
undefined behavior (like signed integer overflow).
CBMC is a bounded model checker, however, which means that the set of all
possible inputs may have to be restricted to all inputs of some bounded size.

The [starter kit overview](https://model-checking.github.io/cbmc-training/starter-kit/overview/index.html)
gives a fairly complete example of how to use the starter kit to add
CBMC verification to an existing software project.

The [starter kit wiki](https://github.com/awslabs/aws-templates-for-cbmc-proofs/wiki)
is currently the primary user guide for the starter kit.

## Installation

The starter kit is distributed as both a brew package and a pip package, and the
[release page](https://github.com/model-checking/cbmc-starter-kit/releases/latest)
gives installation instructions that we repeat here.

### brew installation

On MacOS, we recommend using brew to install the starter kit with
```
brew tap aws/tap
brew install cbmc-starter-kit
```
and upgrade to the latest version with
```
brew upgrade cbmc-starter-kit
```
In these instructions, the first line taps an AWS repository that hosts the starter kit.
The [brew home page](https://brew.sh/) gives instructions for installing brew.

### pip installation

On any operating system with python installed, use pip to install the
starter kit with
```
python3 -m pip install cbmc-starter-kit
```
and upgrade to the latest version with
```
python3 -m pip install --upgrade cbmc-starter-kit
```
The [python download page](https://www.python.org/downloads/) gives instructions
for installing python.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
