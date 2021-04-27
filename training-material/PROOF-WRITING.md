# How to Write a CBMC Proof
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** 

- [The components of a CBMC proof](#the-components-of-a-cbmc-proof)
- [Running example.](#running-example)
- [The Proof harness](#the-proof-harness)
  - [What does a good proof harness look like?](#what-does-a-good-proof-harness-look-like)
  - [How to write a good proof harness](#how-to-write-a-good-proof-harness)
- [The Proof Makefile](#the-proof-makefile)
- [The `is_valid()` function](#the-is_valid-function)
  - [Example of an `is_valid()` function](#example-of-an-is_valid-function)
- [The `ensure_allocated` function](#the-ensure_allocated-function)
- [Stubs and abstractions](#stubs-and-abstractions)
- [How do I add the function contract to the function being verified?](#how-do-i-add-the-function-contract-to-the-function-being-verified)
  - [Example using function contracts](#example-using-function-contracts)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

	
## The components of a CBMC proof

A CBMC proof normally consists of several components:

1. A **proof harness** which:
   1. Sets up required data-structures
   1. Calls the function being verified
   1. Checks any function post-conditions
1. A **proof makefile** which:
   1. Defines any necessary preprocessor defines
	  e.g. `-DMAX_BUFFER_SIZE=10`
   1. Specifies the dependencies of the code under test 
   1. Specifies any abstractions or models used by proof
   
   Much of the work done by these Makefiles is common among proofs.
   We provide a `Makefile.common`, which provides useful makefile rules shared by all proofs.
1. A set of **`_is_valid()` functions**, one for each **datatype** used in the proof
   1. Typically go in the code-base itself
   1. Can be used in the codebase as assertions to improve runtime checking.
   1. Can be reused by multiple proofs
1. A set of **`_allocate()` and `ensure()` functions**,  one for each **datatype** used in the proof
   1. Due to limitations of the CBMC tools, not all properties about a datatype can be declared declaratively.
   In particular, allocation of memory must be done impartively.
   These functions handle allocation of the data-structure, and any recursive substructures.
   1. Can be put in a library and reused by multiple proofs.   
1. A **library of helper functions** which:
   1. Models any external libraries (e.g. libCrypto)
   1. Provides implementations for abstracted functions
   
The remainder of this document describes how build each one of these components.

## Running example.
We will use the `aws_array_list` module from [AWS C Common](https://github.com/awslabs/aws-c-common) open-source project as our running example.
This module provides a polymorphic array defined as follows:

```
struct aws_array_list {
    struct aws_allocator *alloc;
    size_t current_size;
    size_t length;
    size_t item_size;
    void *data;
};
```

* `alloc` represents the allocator used by the list (to allow consumers of the list to override `malloc` if desired)
* `current_size` represents the bytes of memory that the array has allocated
* `length` is the number of items that it contains
* `data_size` represents the size of the objects stored in the list (in bytes)
* `data` points to a byte array in memory that contains the data of the array list.

Users of this data structure are expected to access its fields using getter and setter methods, although C does not offer language support to ensure that they do so.
Similarly, since the C type system does not have support for polymorphism, authors of the getters and setters are responsible for ensuring that the list is accessed safely.
The getter itself is defined as:

```
int aws_array_list_get_at_ptr(const struct aws_array_list *AWS_RESTRICT list, void **val, size_t index) {
    if (aws_array_list_length(list) > index) {
        *val = (void *)((uint8_t *)list->data + (list->item_size * index));
        return AWS_OP_SUCCESS;
    }
    return aws_raise_error(AWS_ERROR_INVALID_INDEX);
}
```

## The Proof harness

### What does a good proof harness look like?

Syntactically, a proof harness looks quite similar to a unit test.
The main difference is that a proof harness calls the target function with a partially-constrained input rather than a concrete value; when symbolically executed by CBMC, this has the effect of exploring the function under *all* possible inputs that satisfy the constraints.

We have developed a style of writing proofs that we believe is readable, maintainable, and modular.
This style was driven by feedback from developers, and addresses the need to communicate *exactly what we are proving* to developers and users.

Our proofs have the following features:

1. They are structured as *harnesses* that call into the function being verified, similar to unit tests.
   This makes them easier to write, because they follow a pattern most developers are familiar with.
   This style also yields more useful error traces.
   Most importantly, it makes proofs easier to understand and maintain, since a developer reviewing a proof has an "executable" which they can understand using their existing knowledge and intuition about C code.
1. They state their assumptions declaratively.
   Rather than creating a fully-initialized data structure in imperative style, we create unconstrained data structures and then constrain them just enough to prove the property of interest.
   This means the only assumptions on the data structure's values are the ones we state in the harness.
1. They follow a predictable pattern: setting up data structures, assuming preconditions on them, calling into the code being verified, and asserting postconditions.


The following code is an example of a proof harness:

```
void aws_array_list_get_at_ptr_harness() {
    /* initialization */
    struct aws_array_list* list = can_fail_malloc(sizeof(*list));
    __CPROVER_assume(list != NULL));
    __CPROVER_assume(aws_array_list_is_bounded(list));
    ensure_array_list_has_allocated_data_member(list);

    /* generate unconstrained inputs */
    void **val = can_fail_malloc(sizeof(void *));
    size_t index;

    /* preconditions */
    __CPROVER_assume(aws_array_list_is_valid(list));
    __CPROVER_assume(val != NULL);

    /* call function under verification */
    if(!aws_array_list_get_at_ptr(list, val, index)) {
      /* If aws_array_list_get_at_ptr is successful,
       * i.e. ret==0, we ensure the list isn't
       * empty and index is within bounds */
        assert(list->data != NULL);
        assert(list->length > index);
    }

    /* postconditions */
    assert(aws_array_list_is_valid(list));
    assert(val != NULL);
}
```


The harness shown above consists of five parts:

1. Initialize the data structure to unconstrained values.
  We recommend initializers for all verified data structures use a consistent naming scheme:
  `ensure_{data_structure}_has_allocated_data_member()`.
1. Generate unconstrained inputs to the function.
1. Constrain all inputs to meet the function specification and assume all preconditions using `assume` statements.
   If necessary, bound the data structures so that the proof terminates.
1. Call the function under verification with these inputs.
1. Check any function postconditions using `assert` statements.

### How to write a good proof harness

We recommend approaching writing a proof-harness as an iterative process:

1. Write a minimally constrained harness, which simply 
   1. declares the necessary variables
   1. and then calls the function under test using them.
   
   For example, for the harness given above, an initial harness might look like:

   ```
   void aws_array_list_get_at_ptr_harness() {
       /* initialization */
       struct aws_array_list* list;

       /* generate unconstrained inputs */
       void **val;
       size_t index;

       /* call function under verification */
       aws_array_list_get_at_ptr(list, val, index);
   }
   ```

   Note that we are leaving the inputs to the function completely unconstrained: we are simply declaring them on the stack, and then using them without assigning any values to them.
   In a normal C compiler, this would be undefined behaviour.
   In CBMC, this is legal, but represents an **unconstrained value** (you may also hear this called a **non-determinstic** value).
   The CBMC tool will use a mathematical solver which considers every possible value of an unconstrained variable.
   If there exists a value which can cause an assertion failure, the solver will find it.
   Conversely, if solver says the assertion cannot be violated, this forms mathematical *proof* that no such value exists.
   
   Leaving these values unconstrained will almost certainly lead to CBMC detecting violations, because real functions have implicit (or, if you're lucky, explicit) constraints on their inputs. 
   For example, it is typically a precondition of a function that pointers must either reference valid memory, or be `null`.
   However, sometimes you may be surprised: if a function doesn't use a given input, or uses it in a defensive way, it may accept totally unconstrained values.
	What we are attempting to do is find the minimum constraint that will allow the function to succeed with no assertion violations.
	So we start with unconstrained values, and slowly constrain them just enough to get the function to verify.
1. Run CBMC and observe the output.
   In the case of our running example, you will see errors that look like this
   
   ```
   Errors
     * In include/aws/common/array_list.inl
       * In aws_array_list_get_at_ptr
         * Line 347:
           * [trace] val != ((void*)0) check failed
   ```
   Consult our [guide to debugging CBMC output](DEBUGGING.md) for suggestions about how to understand this output.
1. Constrain each input in turn until all warnings are resolved.
   See the sections on writing `_is_valid()` and `_ensure_is_allocated()` functions for details on how to do this
1. Fix any loop-unwinding errors.
   To fix these errors, you will need update the Makefile with the correct loop bounds.
   This may cause CBMC to get quite slow.
   In this case, we recommend **bounding** the size of data-structures to allow CBMC to finish quickly.
   In the harness above, this is accomplished by the line
   ```
   __CPROVER_assume(aws_array_list_is_bounded(list))
   ```
   We recommend starting with very small bounds to ensure a quick REPL cycle.
   Once the proof is finished, you can increase the bounds to increase assurance.
1. Check the coverage report.
   Ideally, you will have 100% coverage.
   In practice, coverage will be less than 100%, for e.g. in defensive code that redundantly checks for errors.
   In this case, inspect the uncovered code, and ensure that it matches your expectations.
1. Increase assurance by adding assertions to the harness.
   There are typically three types of such assertions:
   1. Data structures should remain valid, whether or not the function under test succeeded.
   1. If the function failed, data-structures should remain unchanged.
   1. If the function succeeded, data-structures should be updated according to the function semantics.
   
   In our example harness, this is handled by the lines 
```
    /* call function under verification */
    if(!aws_array_list_get_at_ptr(list, val, index)) {
      /* If aws_array_list_get_at_ptr is successful,
       * i.e. ret==0, we ensure the list isn't
       * empty and index is within bounds */
        assert(list->data != NULL);
        assert(list->length > index);
    }

    /* postconditions */
    assert(aws_array_list_is_valid(list));
    assert(val != NULL);
```


## The Proof Makefile

The Makefile for our running example looks like this:

```
# Sufficently long to get full coverage on the aws_array_list APIs
# short enough that all proofs complete quickly
MAX_ITEM_SIZE ?= 2
DEFINES += -DMAX_ITEM_SIZE=$(MAX_ITEM_SIZE)

# Necessary to get full coverage when using functions from math.h
MAX_INITIAL_ITEM_ALLOCATION ?= 9223372036854775808ULL
DEFINES += -DMAX_INITIAL_ITEM_ALLOCATION=$(MAX_INITIAL_ITEM_ALLOCATION)

# This bound allows us to reach 100% coverage rate
UNWINDSET += memcpy_impl.0:$(shell echo $$(($(MAX_ITEM_SIZE) + 1)))

CBMCFLAGS +=

DEPENDENCIES += $(HELPERDIR)/source/proof_allocators.c
DEPENDENCIES += $(HELPERDIR)/source/make_common_data_structures.c
DEPENDENCIES += $(HELPERDIR)/source/utils.c
DEPENDENCIES += $(HELPERDIR)/stubs/error.c
DEPENDENCIES += $(HELPERDIR)/stubs/memcpy_override.c
DEPENDENCIES += $(SRCDIR)/source/array_list.c
DEPENDENCIES += $(SRCDIR)/source/common.c

ENTRY = aws_array_list_get_at_ptr_harness
###########

include ../Makefile.common
```

1. It defines a set of variables that can be used as bounds in the proof.
   As discussed above, we recommend starting with small bounds to enable quick iteration on the proof and increasing them once the proof is complete.
   These variables are created both as Makefile variables, which can be used later (e.g. in the `UNWINDSET`, and also passed as `-D` defines, which allow 
1. It creates an `UNWINDSET` which tells CBMC how many times to unroll loops in the program.
   As shown here, loop bounds typically depend on variables within the makefile.
   Its a good idea to make this explicit, as we do here, to avoid the need to change magic constants as you experiment with the proof.
1. A list of `CBMCFLAGS` if any are needed.
   Typically, all the required flags are set in the `Makefile.common`, and this can be left empty
1. A list of `DEPENDENCIES`, which are the
   1. Project source files
   1. Proof stubs/models [TODO, this really belongs in ABSTRACTIONS]
1. The `ENTRY`, which is the name of the function being verified
1. `include ../Makefile.common` to take advantage of the standard templates declared in that file.

Most makefiles should like exactly like this.
[TODO discuss wellspring, litani]

## The `is_valid()` function

The `is_valid()` functions used in preconditions are developed using an iterative process. 
For each **data-structure** module, start by specifying the simplest predicates that you can think of for the data structure --- usually, that the data of the data structure is correctly allocated.
Then, gradually refine these predicates, until you have a set of reasonable invariants for the data structure.

You can verify that invariants are reasonable by:

1. Having an explicit code-review in which subject matter experts on the development team confirm that the invariants represent the design intent of the code
1. Adding these invariants are pre/post-conditions to the code being verified, and ensuring that all unit and regression tests pass.
   Note that unit-test failures do not necessarily reflect problems with your invariants.
   They may also reflect either 
   1. Bugs in the code itself
   1. Bugs in the unit-tests
   
   In both these cases, fix the bug in the code, then make sure the invariant now succeeds during the tests. 

### Example of an `is_valid()` function

For instance, in the case of the `array_list`, we started
with the invariant that `data` points to `current_size`
allocated bytes.
After several iterations, the validity invariant for `array_list` ended up looking like this:

```
bool aws_array_list_is_valid(const struct aws_array_list *list) {
  if (!list) return false;
  size_t required_size = 0;
  bool required_size_is_valid = (aws_mul_size_checked(list->length, list->item_size, &required_size) == AWS_OP_SUCCESS);
  bool current_size_is_valid = (list->current_size >= required_size);
  bool data_is_valid = ((list->current_size == 0 && list->data == NULL) || AWS_MEM_IS_WRITABLE(list->data, list->current_size));
  bool item_size_is_valid = (list->item_size != 0);

  return required_size_is_valid && current_size_is_valid && data_is_valid && item_size_is_valid;
}
```

The invariant above describes four conditions satisfied by a valid `array_list`:

1. the sum of the sizes of the items of the list must fit in an unsigned integer of type `size_t`, which is checked using the function `aws_mul_size_checked` 
1. the size of the `array_list` in bytes (`current_size`) has to be larger than or equal to the sum of the sizes of its items;
1. the `data` pointer must point to a valid memory location; otherwise it must be `NULL` if the size of the `array_list` is zero;
   This point is actually somewhat subtle: there was debate among the team about whether the pointer must be `NULL`, or whether any value was legal if the length was zero.
   Writing an explicit `is_valid()` function forced the team to come to a precise decision.
1. the `item_size` must be positive.

## The `ensure_allocated` function

Ideally, all properties in a proof harness would be written in a declarative style.
Unfortunately, CBMC currently does offer support that allows code to `__CPROVER_assume()` that memory is correctly allocated.
Instead, it must be allocated using imperative calls to `malloc()`.
By default, CBMC `malloc()` never returns `null`.
So its important that you explicitly handle the case where the pointer might be `null`.

Its important to separate the work done in this function from the work done in an `is_valid` function.
This function should only worry about allocating the memory needed by the data-structure.
Any other validity constraints should be handled by the `is_valid()` check.

The `ensure` function for the running example is:

```
void ensure_array_list_has_allocated_data_member(struct aws_array_list *const list) {
    if (list->current_size == 0 && list->length == 0) {
        __CPROVER_assume(list->data == NULL);
        list->alloc = can_fail_allocator();
    } else {
        list->data = bounded_malloc(list->current_size);
        list->alloc = nondet_bool() ? NULL : can_fail_allocator();
    }
}
```

## Stubs and abstractions

* TODO

## How do I add the function contract to the function being verified?

We strongly recommend adding all checks and assumptions from the proof harness to the function being verified as runtime assertions.
This provides value in several ways.

1. **It connects the code and the proof.**
   Proofs for all but the most simple functions require environment assumptions.
   One of the most common ways proof can go wrong is when these assumptions the real-world context in which the function is used.
   Adding the assumptions as runtime assertions in the code allows such mismatches to be detected as the code runs.
   Some teams choose to enable these assertions only in debug mode; this allows mismatches to be detected during the standard unit and integration testing processes with any performance penalty on production code.
   Other teams enable these assertions for all builds, providing increased assurance at a small runtime cost.
1. **It helps detect bugs in the broader codebase.**
   On a number of occasions, adding function contracts to correct code detected function contracts in other parts of the code base.
   In several cases, we discovered errors in other projects, which were calling verified APIs with invalid parameters.
   Even though those projects had never been formally verified, they still benefited from the function contracts developed during the formal verification work.
1. **It helps focus the mind.**
   It is easy to let standards slip during code-reviews for test and verification code.
   "Even if its not perfect, its better than nothing, so might as well just click approve."
   Adding the proof assumptions and checks to the codebase itself as runtime assertions causes reviewers to take them much more seriously, which leads to both increased proof quality, and improved code quality.

### Example using function contracts

In the running example, our verification harness assumed the following preconditions

```
    __CPROVER_assume(aws_array_list_is_valid(list));
    __CPROVER_assume(val != NULL);
```

These directly translate into preconditions in the function under test:

```
    AWS_PRECONDITION(aws_array_list_is_valid(list));
    AWS_PRECONDITION(val != NULL);
```

Similarly, the key postcondition checked in the verification harness is 

```
    assert(aws_array_list_is_valid(list))
```

This also directly translates into a postcondition in the function under test:

```
    AWS_POSTCONDITION(aws_array_list_is_valid(list));
```

Putting it all together: 

```
int aws_array_list_get_at_ptr(
        const struct aws_array_list* list,
        void **val,
        size_t index)
{
    AWS_PRECONDITION(aws_array_list_is_valid(list));
    AWS_PRECONDITION(val != NULL);
    if (aws_array_list_length(list) > index) {
        *val = (void *)((uint8_t *)list->data +
                        (list->item_size * index));
        AWS_POSTCONDITION(aws_array_list_is_valid(list));
        return AWS_OP_SUCCESS;
    }
    AWS_POSTCONDITION(aws_array_list_is_valid(list));
    return aws_raise_error(AWS_ERROR_INVALID_INDEX);
}
```
