# Getting started with the CBMC starter kit

The [CBMC starter kit](https://github.com/model-checking/cbmc-starter-kit) makes
it easy to add CBMC verification to an existing software project.

[CBMC](https://github.com/diffblue/cbmc) is a model checker for
C. This means that CBMC will explore all possible paths through your code
on all possible inputs, and will check that all assertions in your code are
true.
CBMC can also check for the possibility of
memory safety errors (like buffer overflow) and for instances of
undefined behavior (like signed integer overflow).
CBMC is a bounded model checker, however, which means that the set of all
possible inputs may have to be restricted to all inputs of some bounded size.

For a quick start on using the starter kit, see

* [Installation](installation)
* [Tutorial](tutorial)