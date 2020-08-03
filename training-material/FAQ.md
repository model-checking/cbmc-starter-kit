#CBMC FAQ

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** 

- [How should I select the initial entry-point to verify?](#how-should-i-select-the-initial-entry-point-to-verify)
  - [Top down approach](#top-down-approach)
  - [Bottom up approach](#bottom-up-approach)
- [How do I set up the tools I need?](#how-do-i-set-up-the-tools-i-need)
- [How do I set up my repository for verification?](#how-do-i-set-up-my-repository-for-verification)
- [How do I write a good proof harness?](#how-do-i-write-a-good-proof-harness)
- [How do I write function pre/post conditions?](#how-do-i-write-function-prepost-conditions)
- [How do I write a proof Makefile?](#how-do-i-write-a-proof-makefile)
- [How do I write a good ensures function?](#how-do-i-write-a-good-ensures-function)
- [How should I write a good is_valid function?](#how-should-i-write-a-good-is_valid-function)
- [I see 12 proof failures. How do I select which one to debug?](#i-see-12-proof-failures-how-do-i-select-which-one-to-debug)
- [How do I debug a proof failure?](#how-do-i-debug-a-proof-failure)
- [What are some examples of good CBMC proofs?](#what-are-some-examples-of-good-cbmc-proofs)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## How should I select the initial entry-point to verify?
There are two basic approaches that we have used at AWS to verify C code using CBMC: **top down**, and **bottom up**.
In our experience, the top-down approach is best suited to a 

### Top down approach
The top-down approach begins by selecting the most critical entry-points into the code.
For example, when verifying an HTTP library, you might choose to begin with the network parser that handles data directly off the wire.
Since this parser is directly exposed to untrusted input, verification leads to a significant security benefit.

* Advantages:
 * Can be useful in cases where there is a limited amount of time to complete as much useful verification as possible, for example to before an upcoming feature release.
 * Focus directly on the most security/safety critical portions of the code
* Disadvantages: 
 * Proofs can be very large, and tax the performance limits of CBMC
 * Can require writing a large number of initializer functions
 * Can require writing a large number of validity predicates
 * Little opportunity to reuse work.

### Bottom up approach

The bottom-up approach follows the natural dependency flow of the codebase being verified.
In our experience, the more self-contained a piece of code is, the easier it is to verify.

1. Make a dependency graph of the modules in your program.
2. Select the leaves of the graph - those modules which other modules depend upon, but which do not depend on other modules themselves.
   Typically, these include the basic data-structures and algorithms used by the rest of the codebase.
   Which one of these you choose is a matter of style: you can use the [TODO, link to coding guidelines] coding guidelines to help select modules which are likely to be good verification targets.
3. Inside a given module, select the best initial verification target.
   This is often, but not always, one of the simpler functions.
   In particular, you are looking for a function which is both easy to verify, and will give good insight into the data-structure invariants of the data-structures used in the given module.
   In our experience, it often makes sense to start with allocation or initialization functions (which often have named that end in `_alloc()` or `_init()`
   
## How do I set up the tools I need?
[TODO] - basically brew install / apt-get install. Link to that page.

## How do I set up my repository for verification?
We have created a "Proof Starter Kit" repository, which includes the basic information required to set up a build-system for your first proof.

1. Select where the proofs, and related artifacts, will go.
   Most projects put them parallel to existing verification artifacts.[TODO, should we retire .cbmc_batch, and move it to tests/cbmc? for all projects]
   For example, if your project has folders `project/tests/unit`, `projects/tests/integration`, and `projects/tests/fuzzing`, we would suggest adding a folder `project/tests/cbmc`.
1. Add the "CBMC Proof Starter Kit" repository, available at [TODO], to the `/cbmc` folder as a submodule.
   Use the command `[TODO]`.
   This will install a standard makefile, as well as a set of useful utility files.
   Follow the documentation in that repository to set any needed project specific overrides in the makefile.
1. Create the folders:
 1. `tests/cbmc/proofs`
 1. `tests/cbmc/stubs`
 1. `tests/cbmc/include`
 1. `tests/cbmc/source`
1. Choose an initial proof target `functionname` following the instructions above.
   We recommend choosing as simple a function as possible to verify in this case.
   This forms a "tracer bullet" proof to ensure that your infrastructure is working correctly.
1. Create the folder `tests/cbmc/proofs/functionname`
 1. Copy the sample proof makefile, and the sample proof harness, into that folder from the "proof starter kit" repo, and fill in the blanks.
    How to actually write the proof is discussed below [TODO link]
1. Follow the instructions at [TODO where??] to enable CBMC CI for your repository


## How do I write a good proof harness?
We have developed a style of writing proofs that we believe is readable, maintainable, and modular.
This style was driven by feedback from developers, and addresses the need to communicate *exactly what we are proving* to developers and users.

Our proofs have the following features:
1. They are structured as *harnesses* that call into the function being verified, similar to unit tests.
   This makes it easy to see how they work, as developers can `execute' the proof in their heads.
   This style also yields more useful error traces.
1. They state their assumptions declaratively.
   Rather than creating a fully-initialized data structure in imperative style, we create unconstrained data structures and then constrain them just enough to prove the property of interest.
   This means the only assumptions on the data structure's values are the ones we state in the harness.
1. They follow a predictable pattern: setting up data structures, assuming preconditions on them, calling into the code being verified, and asserting postconditions.

The following code is an example of a proof harness:

```
void aws_array_list_get_at_ptr_harness() {
    /* initialization */
    struct aws_array_list list;
    __CPROVER_assume(aws_array_list_is_bounded(&list));
    ensure_array_list_has_allocated_data_member(&list);

    /* generate unconstrained inputs */
    void **val = can_fail_malloc(sizeof(void *));
    size_t index;

    /* preconditions */
    __CPROVER_assume(aws_array_list_is_valid(&list));
    __CPROVER_assume(val != NULL);

    /* call function under verification */
    if(!aws_array_list_get_at_ptr(&list, val, index)) {
      /* If aws_array_list_get_at_ptr is successful,
       * i.e. ret==0, we ensure the list isn't
       * empty and index is within bounds */
        assert(list.data != NULL);
        assert(list.length > index);
    }

    /* postconditions */
    assert(aws_array_list_is_valid(&list));
    assert(val != NULL);
}
```


The harness shown above consists of five parts:

1. Initialize the data structure to unconstrained values.
  We developed initializers for all verified data structures using a consistent naming scheme:
  `ensure_{data_structure}_has_allocated_data_member()`.
1. Generate unconstrained inputs to the function.
1. Constrain all inputs to meet the function specification and assume all preconditions using `assume` statements.
   If necessary, bound the data structures so that the proof terminates.
1. Call the function under verification with these inputs.
1. Check any function postconditions using `assert` statements.

This style of writing a proof harness is motivated by our desire to make assumptions explicit to developers.
This style consists of two steps.
The first step does the minimal work required to imperatively allocate
structures with unconstrained fields, as described in Items 1 and 2 in the above list.
The second step uses `assume` statements to enforce
the specification about the values that go in those fields (Item 3).
This makes the specification used in the proof harness clear and allows them to be further reused as assertions in the mainline code.

Syntactically, a proof harness looks quite similar to a unit test.
The main difference is that a proof harness calls the target function with a partially-constrained input rather than a concrete value; when symbolically executed by CBMC, this has the effect of exploring the function under *all* possible inputs that satisfy the constraints.

In fact, historically, we started from unit tests, and tried to make them symbolic by replacing concrete values with unconstrained values.
We found this difficult, since there are relations that constrain fields in a data structure and must be enforced (e.g., `length < capacity` and `capacity != 0 IMPLIES buffer != 0`).
Even worse, these imperative proof-harnesses turned out to be difficult to reason about and to explain to the development team.

## How do I write function pre/post conditions?

The preconditions used as assumptions in (Item $(3)$) are developed using an iterative process. 
For each module, we start by specifying the simplest predicates that we can think of for the data structure --- usually, that the data of the data structure
is correctly allocated.
Then we gradually refine these predicates, until the development team accepts them as reasonable invariants for the data structure, aided by having all the unit and regression tests pass.

Using this process, we defined a set of predicates for each data structure in the C
source file so that they can be easily accessed and modified by the library
developers, and so that they serve as documentation for the library's users.
For instance, in the case of the `array_list`, we started
with the invariant that `data` points to `current_size`
allocated bytes.
After several iterations, the validity invariant for `array_list` ended up looking like this:

```
bool aws_array_list_is_valid(
       const struct aws_array_list *list) {
  if (!list) return false;
  size_t required_size = 0;
  bool required_size_is_valid =
      (aws_mul_size_checked(list->length,
                            list->item_size,
                            &required_size)
       == AWS_OP_SUCCESS);

  bool current_size_is_valid =
      (list->current_size >= required_size);
  bool data_is_valid =
      ((list->current_size == 0 && list->data == NULL)
      || AWS_MEM_IS_WRITABLE(list->data, list->current_size));
  bool item_size_is_valid = (list->item_size != 0);

  return required_size_is_valid
      && current_size_is_valid
      && data_is_valid && item_size_is_valid;
}
```

The invariant above describes four conditions satisfied by a valid `array_list`:

1. the sum of the sizes of the items of the list must fit in an unsigned integer of type `size_t`, which is checked using the function `aws_mul_size_checked` 
1. the size of the `array_list` in bytes (`current_size`) has to be larger than or equal to the sum of the sizes of its items;
1. the `data` pointer must point to a valid memory location, otherwise it must be `NULL` if the size of the `array_list` is zero;
1. the `item_size` must be positive.

## How do I write a proof Makefile?

## How do I write a good ensures function?

## How should I write a good is_valid function?


## I see 12 proof failures. How do I select which one to debug?
CBMC proof failures seem to come in batches: you run the proof, and see a dozen different errors reported
In many cases, these failures are related: instead of stressing about the number of failures, pick one, debug it, and see if fixing it removes (many of) the others.
Some good heuristics for deciding which failure to investigate:

1. Look for a failure that occurs early on in the proof.
   This will often be the one with the shortest trace [TODO viewer should output this information].
   The shorter the trace leading to the issue, the easier it is to debug.
   
1. Look for a failure in code you understand.
   Some functions are simpler than others: a failure in a simple function is often easier to analyze that one in a complicated function.
   And a failure in a function you understand is easier than one in 

1. Look for a simple type of failure.
   For example, the trace from a null dereference is often easier to follow than the trace for a use of a DEAD pointer.
   But they're normally exactly the same bug!
   
## How do I debug a proof failure?

There are a number of techniques that have proven useful in debugging proof failures.



## What are some examples of good CBMC proofs?


[AWS-C-Common - Array List Copy](https://github.com/awslabs/aws-c-common/blob/master/.cbmc-batch/jobs/aws_array_list_copy/aws_array_list_copy_harness.c
)

[s2n: stuffer erase and read bytes](https://github.com/awslabs/s2n/blob/master/tests/cbmc/proofs/s2n_stuffer_erase_and_read_bytes/s2n_stuffer_erase_and_read_bytes_harness.c)



