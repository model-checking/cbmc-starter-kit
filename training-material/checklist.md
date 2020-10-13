# A proof checklist for writers and reviewers

This is a check list intended for

* proof writers to use before checking a proof into a repository and
* proof reviewers to use during the code review of a pull
  request containing a proof.

This check list is intended to ensure clear answers to two questions:

* What properties are being checked by the proof?
* What assumptions are being made by the proof?

and that these answers can be found in one of three places:

* The proof harness,
* The proof makefiles (and, with the starter kit, these makefiles are
  the proof Makefile, the project Makefile-project-defines,
  and the project Makefile.common), and perhaps
* The proof readme file.

The best practices for writing a proof are described
in the section [How to Write a CBMC Proof](PROOF-WRITING.md)
of the [training material](README.md)
in this [starter kit](../README.md).
Reviewers should keep these best practices in mind when reading a proof.
We recommend that any deviations from best practices be explained in the
readme file.

## Properties checked

Check the following:

* All of the standard property-checking flags are used:

	* --bounds-check
	* --conversion-check
	* --div-by-zero-check
	* --float-overflow-check
	* --malloc-fail-null
	* --malloc-may-fail
	* --nan-check
	* --pointer-check
	* --pointer-overflow-check
	* --pointer-primitive-check
	* --signed-overflow-check
	* --undefined-shift-check
	* --unsigned-overflow-check

  Note that the starter kit uses these flags by default.
  Note, however, that a developer may disable any one of these flags
  by editing project Makefile.common or
  by setting a makefile variable to the empty string
  (as in `CBMC_FLAG_MALLOC_MAY_FAIL = `)
  in the project Makefile-project-defines or a proof Makefile.
  These are the places to look for deviations.

* All deviations from the standard property-checking flags are documented.

  There are valid reasons to omit flags either for a project or for an
  individual proof. But the decision and the reason for the decision
  must be documented either in a project readme or a proof readme file.

CBMC checks assertions in the code.  This is understood and need not be
documented.

## Assumptions made

Check the following:

* All nontrivial data structures have an
  [`ensure_allocated` function](PROOF-WRITING.md#the-ensure_allocated-function)
  as described in the training material.

  Feel free to use any naming scheme that makes sense for your project --- some
  projects use `allocate_X` in place of `ensure_allocated_X` --- but be
  consistent.

* All nontrivial data structures have an
  [`is_valid()` predicate](PROOF-WRITING.md#the-is_valid-function)
  as described in the training material for every nontrivial data structure.

* All definitions of `ensure_allocated` functions and `is_valid` predicates
  appear in a common location.

  These definitions are most commonly stored in the `proofs/sources`
  subdirectory of the starter kit. Definitions are stored here and used
  consistently in the proofs.

* All pointers passed as input are allocated on the heap with `malloc`.

  One common mistake is to allocate a buffer `buf` on the stack and to
  pass `&buf` to the function under test in the proof harness.  This prevents
  the proof from considering the case of a NULL pointer.

* All instances of `__CPROVER_assume` appear in a proof harness.

  Note that some exceptions are required.  For example, it may be necessary
  in an `ensure_allocated` to assume `length < CBMC_MAX_OBJECT_SIZE` before
  invoking `malloc(length)` to avoid a false positive about malloc'ing a
  too-big object. But every instance of `__CPROVER_assume` in supporting code
  should be copied into the proof harness.  The goal is for all proof
  assumptions to be documented in one place.

* All preprocessor definitions related to bounds on input size or
  otherwise related to proof assumptions appear in the proof Makefile.

  In particular, do not embed definitions in the supporting code or header
  files. The goal is for all proof assumptions to be documented in one place.

* Confirm that all stubs used in the proof are acceptable abstractions
  of the actual code.

  Acceptable could mean simply that every behavior of the original code
  is a behavior of the abstraction.

## Results checked

Look at the report in the checks attached to the pull request.

* Confirm that the coverage is acceptable and confirm that the readme file
  explains the reason for any lines not covered.

* Confirm that the list of missing functions is acceptable.

* Confirm that there are no errors reported.

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
