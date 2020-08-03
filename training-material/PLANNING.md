# CBMC Proof Planning

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** 

- [How to select what proofs to attempt, in what order](#how-to-select-what-proofs-to-attempt-in-what-order)
- [How to get a sense of the work CBMC will involve](#how-to-get-a-sense-of-the-work-cbmc-will-involve)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## How to select what proofs to attempt, in what order

1. Make a dependency graph of the modules in your program.
   There are a number of tools that can help with this, including [doxygen](https://www.doxygen.nl/manual/).
   In addition, you can manually determine a good approximation to the dependency graph using the `.h` files.
   If a module includes the `.h` file of another module, it likely depends on it.
2. Select the leaves of the graph - those modules which other modules depend upon, but which do not depend on other modules themselves.
   Typically, these include the basic data-structures and algorithms used by the rest of the codebase.
   Which one of these you choose is a matter of style: you can use the  [guidelines for coding for verification](CODING-FOR-VERIFICATION.md) to help select modules which are likely to be good verification targets.
3. Inside a given module, select the best initial verification target.
   This is often, but not always, one of the simpler functions.
   In particular, you are looking for a function which is both easy to verify, and will give good insight into the data-structure invariants of the data-structures used in the given module.
   The more a function conforms to our [guidelines for coding for verification](CODING-FOR-VERIFICATION.md), the easiest it will be to verify.
   In our experience, it often makes sense to start with allocation or initialization functions (which often have named that end in `_alloc()` or `_init()`.
4. The first proof for a given module is typically the hardest.
   It typically requires the creation of an `_is_valid()` function and an `_ensure_is_allocated()` function.
   However, once these have been written once, the remainder of the module becomes much easier.
   The amount of time needed to complete a proof can vary significantly, from hours for a simple proof to days for a complex one.
   If the function has few dependencies, and conforms to the guidelines for coding for verification, we would expect an initial proof to take perhaps a day's work.[TODO I made up this number.  We need data]
   If it is taking longer than this, try a different entry-point.
   
## How to get a sense of the work CBMC will involve

We recommend selecting a few (2-3) modules from the leaves of the dependency graph, and then doing 2-3 proofs from each module.
This will give you a sense of 

1. How much work the first proof in a new module is
1. How much work subsequent proofs in that module is, once the `_is_valid()` and `_ensure_is_allocated()` functions are written.

Predicting precisely how hard a piece of code will be to verify can be difficult.
In general, however, the more code conforms to our [guidelines for coding for verification](CODING-FOR-VERIFICATION.md), the easier it will be to verify.
We recommend trying  modules of different verification complexity to get a sense of overall expected effort.

Particular features to look for are:

1. Does the code have loops?
   1. If so, are those loops nested? 
      Since CBMC unrolls loops before verifying them, nested loops can lead to a quadratic (or worse) increase in the amount of work CBMC will need to perform.
   1. Are they over fixed sizes, or do they vary with the size of inputs?
      If loops are of fixed size, it may be hard to simplify the problem if CBMC is having performance issues as the proof is being developed.
	  On the other hand, once the proof is complete, functions with fixed-sized loops may have higher assurance proofs, since data-structures do not need to be bounded for performance reasons.
1. Does the code use inductive data-structures (e.g. linked lists, trees)?
   Inductive data-structures are much harder to model and verify than linear structures such as arrays.
1. Does the code have function pointers?
   Function pointers are hard to model.
   They can also cause performance problems for CBMC.
1. Does the code have an simple and obvious specification?
   One of the main challenges in verification is writing the specification.
   The simpler the specification of the code being verified, the easier it is to verify.
   Similarly, the better the documentation, the easier it is.
   
   
