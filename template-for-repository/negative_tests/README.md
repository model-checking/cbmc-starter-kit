## Negative Tests

This directory contains negative checks to ensure that CBMC CI jobs are run
with the complete set of property-checking flags
(see `CHECKFLAGS` in [Makefile.common](../proofs/Makefile.common))
which we consider to be part of the best practice.

To enable these tests in CI jobs,
copy this (`negative_tests`) directory into `../proofs`.

If a property-checking flag is not used used by your project,
you might want to disable the corresponding negative test.
To do so, simply delete the particular test directory from `../proofs/negative_tests`.
