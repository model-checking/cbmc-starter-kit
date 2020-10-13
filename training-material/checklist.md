# A proof checklist for writers and reviewers

This is a check list of best practices intended

* for proof writers to use before checking a proof into a repository and
* for proof reviewers to use during the code review of a pull
  request containing a proof.

The best practices for writing a proof are already described in detail
in the section [How to Write a CBMC Proof](PROOF-WRITING.md)
of the [training material](README.md)
win this [starter kit](../README.md).

There are two questions whose answers must be absolutely clear:

* What properties are being checked by the proof?
* What assumptions are being made by the proof?

These answers should be found in one of three places:

* The proof harness,
* The proof makefiles (and, with the starter kit, these makefiles are
  the proof Makefile, the project Makefile-project-defines,
  and the project Makefile.common), and perhaps
* The proof readme file.

## Properties checked

* Run cbmc with the following property-checking flags

	* --malloc-may-fail
	* --malloc-fail-null
	* --bounds-check
	* --conversion-check
	* --div-by-zero-check
	* --float-overflow-check
	* --nan-check
	* --pointer-check
	* --pointer-overflow-check
	* --pointer-primitive-check
	* --signed-overflow-check
	* --undefined-shift-check
	* --unsigned-overflow-check

  The starter kit uses these flags by default.  But the user of the starter kit
  may disable any one of these flags by editing project Makefile.common or
  by setting a makefile variable to the empty string
  (as in `CBMC_FLAG_MALLOC_MAY_FAIL = `)
  in the project Makefile-project-defines or a proof Makefile.

* Document the decision to omit one of these property-checking flags.
  There are valid reasons to omit them either for a project or for an
  individual proof. But the decision and the reason for the decision
  must be document either in a project readme or a proof readme file.

* CBMC checks assertions in the code.  This is understood and need not be
  documented.

## Assumptions made

* Define an
  [`ensure_allocated` function](PROOF-WRITING.md#the-ensure_allocated-function)
  as described in the training material for every nontrivial data structure.
  Feel free to use any naming scheme that makes sense for your project --- some
  projects use `allocate_X` in place of `ensure_allocated_X` --- but be
  consistent.

* Define an
  [`is_valid()` predicate](PROOF-WRITING.md##the-is_valid-function)
  as describe in the training material for every nontrivial data structure.

* Gather the definitions of `ensure_allocated` and `is_valid` in a common
  location, most commonly in the `proofs/sources` subdirectory of the
  starter kit.

* Check that every instance of `__CPROVER_assume` appears either a proof
  harness. Some exceptions are required.  For example, it may be necessary
  in an `ensure_allocated` to assume `length < CBMC_MAX_OBJECT_SIZE` before
  invoking `malloc(length)` to avoid a false positive about malloc'ing a
  too-big object. But every instance of `__CPROVER_assume` in supporting code
  could be copied into the proof harness.  The goal is for all proof
  assumptions to be documented in one place.

* Check that every preprocessor definition related to bounds on input size or
  otherwise related to proof assumptions is defined in the proof Makefile.
  In particular, do not embed definitions in the supporting code or header
  files. The goal is for all proof assumptions to be documented in one place.

## Other things to consider

* Consider writing function contracts for the function under test as
  described in [How to Write a CBMC Proof](PROOF-WRITING.md)
  of the [training material](README.md).
  The check list above ensures that the properties (including the
  assumptions about the input) that must be true before function
  invocation are clearly stated in the proof harness. Consider adding
  a statement of what properties must be true after function invocation
  as assertions at the end of the proof harness.

* Consider adding the assumptions made by the proof harness for a
  function under test to the source code for the function in the form
  of assertions in the code. This will validate that the assumptions made
  by the proof of a function are satisfied by each invocation of the function
  (at least during testing).
