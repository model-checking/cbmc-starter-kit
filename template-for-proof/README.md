<__FUNCTION_NAME__> proof
==============

This directory contains a memory safety proof for <__FUNCTION_NAME__>.

To run the proof.
* Add cbmc, goto-cc, goto-instrument, goto-analyzer, and cbmc-viewer
  to your path.
* Run "make".
* Open html/index.html in a web browser.

Getting started with Makefiles using `arpa`
-------------

The [`arpa`](https://github.com/awslabs/aws-proof-build-assistant) tool helps you get started with writing proof Makefiles.

To use `arpa`.
* Run "make arpa" to generate a Makefile.arpa that contains relevant build information for the proof.
* Use Makefile.arpa as the starting point for your proof Makefile by:
  1. Modifying Makefile.arpa (if required).
  2. Including Makefile.arpa into the existing proof Makefile.
