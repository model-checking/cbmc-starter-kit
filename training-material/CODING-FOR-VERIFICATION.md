# CBMC Coding Guidelines

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** 

- [Code Organization to Support Verification](#code-organization-to-support-verification)
- [Improving Verification Performance](#improving-verification-performance)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


The basic principles of coding for verification are similar to those of coding for testability, with some modifications due to the nature of the SAT solver underlying CBMC.

## Code Organization to Support Verification

* Write small functions. Functions should:
  * Do exactly one thing.
  * Take all their input and outputs through function parameters and rely as little as possible on global state. Where possible, avoid global variables.
* Encapsulate interaction with the environment within a small function. Interaction with the environment includes accessing files, the network, etc. This makes is possible to verify that function independently and then stub it out for the rest of the verification.
* Functions should check their input parameters, and return an error code when they fail to verify.
This makes harnesses much simpler, since any value for the parameters is a valid input to the function.
* Avoid unbounded loops as far as possible, and encapsulate the ones that you need.  CBMC does bounded model checking, so we need to be able to compute a bound on the number of iterations of any given loop.  Loops that iterate a constant number of times are best.   Loops whose iteration depends on input will require making some assumptions about the input.
* Consider defining magic numbers that control loop bounds and buffer sizes in your build system, i.e., `-DBUFFER_SIZE=1024` and similar. This ensures that you can configure this value at build time, and we can also use those values in our proofs.
* Provide an easy way to access static functions and data structures for testing, if you must have them. For example, use a macro that overrides static.
* Make threads independently verifiable. When writing concurrent programs, reduce interaction to well-defined points. This enables verification of each thread in isolation.

## Improving Verification Performance

* Avoid void pointers (`void*`). There are two reasons people use void pointers:
  * To hide implementation detail.  This use of void pointers is unnecessary, because we can replace `void *bar` with `struct foo *bar` and declare `struct foo` later within the implementation.
  * To implement a form of polymorphism.  Don't do this for gratuitous reasons (e.g., because it might someday be useful).  Void pointers can block constant propagation which can dramatically reduce the size of the formula constructed for the constraint solver.
* Avoid function pointers. When unavoidable, ensure that function pointer types have a unique signature. They really can make the difference between a proof and no proof.  When CBMC encounters a function pointer, it has to consider all possibilities for what that function could be, based on loose signature matching.  CBMC has to consider possible any function in the entire program whose address is taken with a signature matching the function pointer.  So for each function invocation, the symbolic execution of a single function is replaced with the symbolic execution of a collection of functions (including the functions they call), and the combinatorial explosion makes the size of the formula too big for memory. The worst thing you can do is to give your functions the signature `void foo(void *arg)`; see the point above about avoiding `void*`.
* Large (more than several kB in size) arrays can cause trouble. Again, defining the sizes of arrays in the build system means that we can cleanly re-define them to smaller bounds for our proofs.
* Data-structures should explicitly carry their size, as a parameter (e.g., Pascal strings are better than C strings).
* Stay type safe.
  * Allocate the correct size of objects. Don't use smaller structs when you're only using some fields.
* Consider encapsulating loops in a function, or even just the loop body. Nested loops can lead to a combinatorial explosion in the size of the formula sent to the constraint solver.  Encapsulated loops can be specified and validated in isolation, and the simpler specification can be used in place of the function in the rest of the validation.
* Try to minimize string comparisons
 * E.g., instead of making a `string->string` hash table, consider an `enum->string` hash-table.
