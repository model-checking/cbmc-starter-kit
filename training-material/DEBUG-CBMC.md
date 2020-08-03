# Debugging CBMC issues

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** 

- [I see 12 proof failures. How do I select which one to debug?](#i-see-12-proof-failures-how-do-i-select-which-one-to-debug)
- [How do I debug a proof failure?](#how-do-i-debug-a-proof-failure)
  - [Read the trace](#read-the-trace)
  - [Add additional information to the trace](#add-additional-information-to-the-trace)
  - [Delta debugging](#delta-debugging)
  - [Add assertions to check your hypotheses.](#add-assertions-to-check-your-hypotheses)
  - [Use `assert(0)` to dump program state leading to a checkpoint](#use-assert0-to-dump-program-state-leading-to-a-checkpoint)
  - [Use `assume(...)` to block uninteresting paths](#use-assume-to-block-uninteresting-paths)
  - [Consider the possibility it is a fault in the code itself](#consider-the-possibility-it-is-a-fault-in-the-code-itself)
- [How do I improve proofs with low coverage?](#how-do-i-improve-proofs-with-low-coverage)
  - [Fix any CBMC errors](#fix-any-cbmc-errors)
  - [Check for truly unreachable code.](#check-for-truly-unreachable-code)
  - [Check for over-constrained inputs](#check-for-over-constrained-inputs)
- [How can I tell if my proof is over-constrained?](#how-can-i-tell-if-my-proof-is-over-constrained)
- [What should I do if CBMC crashes?](#what-should-i-do-if-cbmc-crashes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## I see 12 proof failures. How do I select which one to debug?
CBMC proof failures seem to come in batches: you run the proof, and see a dozen different errors reported
In many cases, these failures are related: instead of stressing about the number of failures, pick one, debug it, and see if fixing it removes (many of) the others.
Some good heuristics for deciding which failure to investigate:

1. **Look for a failure that occurs early on in the proof.**
   This will often be the one with the shortest trace [TODO viewer should output this information].
   The shorter the trace leading to the issue, the easier it is to debug.   
1. **Look for a failure in code you understand.**
   Some functions are simpler than others: a failure in a simple function is often easier to analyze that one in a complicated function.
   And a failure in a function you understand is easier than one in a function you are not familiar with.
1. **Look for a simple type of failure.**
   For example, the trace from a null dereference is often easier to follow than the trace for a use of a DEAD pointer.
   But they're normally exactly the same bug!
   Since null dereference bugs normally give the simplest traces, start with them first.
   Often, resolving the null dereference also fixes the other related bugs.
      
## How do I debug a proof failure?

There are a number of techniques that have proven useful in debugging proof failures.

### Read the trace

[TODO link to a guide to viewer]
CBMC viewer generates a step-by-step trace that leads to the assertion violation.
This trace details

* Every line of code executed 
* Every function call made
* Every time a variable is assigned

Essentially, this trace contains everything you would get from attaching a debugger to the program, and single stepping until the violation occurred.
Take a look at the values of the relevant variables right before the assertion violation.
Do they make sense?
If not, figure out where they were assigned.
I often find that `Ctrl-F` is my friend here: I search for either the variable name, or the value it was assigned, and see where it appears in the trace.

Similarly, look at the set of function calls that led to the error.
Do they make sense?
Are there functions you expect to see there, but don't?
Are there functions you didn't expect to see there, but do?

### Add additional information to the trace
The trace has all the information you need to understand the state of program memory at every point during the execution.
But its not always that easy to reconstruct.
In particular, the trace records the value of a variable when it is written to.
But it doesn't record the value of a variable that is only read, or passed along to another function.

You can solve this by adding "dummy writes" to the program.
For example, let's say you were debugging an error that involved the following function

```
int foo(struct bar* b, int x) {
    baz(b->data, x);
}
```

Figuring out the value of `b->data` and `x` are possible given a complete trace, but its difficult.
Any it might harder to figure out the value of `b->size`.
Instead, annotate the code to track those values:

```
int foo(struct bar* b, int x) {
	struct bar debug_foo_b = *b;
	int debug_foo_x = x;
    baz(b->data, x);
}
```

the trace will now contain an assignment to `debug_foo_b`, which will let you see what values each member of the struct had.

### Delta debugging

[Delta debugging](http://web2.cs.columbia.edu/~junfeng/09fa-e6998/papers/delta-debug.pdf) is a powerful technique for localizing faults and creating minimal reproducing test-cases.
Essentially, you modify the program in some way, typically either by removing (commenting out) or modifying code.
You then rerun the verification tool, and see if the results changed.
The goal is to either:

1. produce a small program which still displays the bug or
1. produce a small change between two programs, one of which has the bug, and the other doesn't.

In case 1, you now have a small program which is hopefully easy to understand;
In case 2, you have a small change which induces the bug, and hopefully leads you toward the root cause.

### Add assertions to check your hypotheses.

For example, consider the case of a null pointer dereference of a pointer `p`.
It is important to distinguish the case where the pointer *must* be null, vs the case where it *may* be null, vs the case where it *is never* null.
You can test for these cases by adding `assert(p)` to the function.
If the can be null, the assertion will trigger.
If it cannot be null, the assertion will succeed.

Now, check `assert(!p)` instead.
If can be non-null, this assertion will fail.
If it can only be null, this assertion will succeed.

You now know which one of the three cases is true.
And you can use the trace to see why it can be null/non-null.

You can do similar things to determine why a branch is reachable, or unreachable.

### Use `assert(0)` to dump program state leading to a checkpoint

Sometimes, you want to know how/whether a particular line of code is reachable.
One easy way to learn that is to put `assert(0)` right before the line.
CBMC will detect the assertion violation, and give a trace explaining how it reached there, and with what values.
If the assertion passes without error, you know that the line is unreachable given the current proof harness.

### Use `assume(...)` to block uninteresting paths

There are often many possible execution paths that reach a given line of code / assertion.
Some of these may reflect cases you are trying to understand, while others do not help with your current debugging plan.
Left to its own devices, CBMC will non-deterministically choose one of those traces, which may not be the one you want.
You can guide CBMC to the trace you want by sprinkling `__CPROVER_assume()` statements within the code.
For example, you might `__CPROVER_assume()` that a function fails with an error code, to test whether the calling function handles that error code correctly.
Or you might `__CPROVER_assume()` that a given variable is null, to simplify you search for the root cause of a null dereference.

### Consider the possibility it is a fault in the code itself

In many cases, the error detected by CBMC represents a true issue within the code itself.
This is particularly common in the case of functions which fail to validate their inputs.
In this case, the fix is either to validate the inputs, and return an error if given invalid inputs, or to document the requirements on the inputs, and state that actions on illegal inputs are undefined behaviour.
Which solution you choose depends on the risk profile of the code.

It is also common that code being verified has integer-overflows and other errors that only occur in unusual circumstances.
In these cases, the solution is to either guarantee that inputs are sufficiently small to prevent these issues, or to use overflow-safe builtins, such as gcc's `__builtin_mul_overflow` (documented [here](https://gcc.gnu.org/onlinedocs/gcc/Integer-Overflow-Builtins.html)).

## How do I improve proofs with low coverage?

### Fix any CBMC errors
Make sure that there are no missing function definitions, or property violations.
Both of these errors can affect coverage calculations.

### Check for truly unreachable code.

In some cases, code may be truly unreachable - for example, redundant defensive checks.
Or this may be code which is sometimes reachable, but not in the context of your proof.
For example:
   
```
int size_from_enum(type_enum t) {
	switch (t) {
	case BAR: return 1;
	case BAZ: return 2;
	...
}
   
int function_being_tested() {
	return size_from_enum(BAZ);
}
```
   
   In this case, most of the lines in `size_from_enum` will appear to be unreachable, even though the proof has full coverage of all truly reachable paths.
   
### Check for over-constrained inputs

Consider the case where one side of a branch is not reached, or where execution does not continue past an assumption.
In this case, it is possible that the inputs have been over-constrained 


## How can I tell if my proof is over-constrained?

This will normally appear in coverage - overconstrained proofs will normally have unreachable portions of code.
You can also add a "smoke test", but adding assertions that you expect to fail to the code (which can be as simple as `assert(0)`).
If these assertions do not fail, then sometime is wrong with your proof.

## What should I do if CBMC crashes?

1. Make a new branch, containing the exact code that caused cbmc to crash.
   We recommend giving it a name like `cbmc-crashing-bug-1`.
1. Push it to public github repo (if possible)
1. Post a bug report [here](https://github.com/diffblue/cbmc/issues/new), linking to the branch that you pushed containing the bug.
1. Post a bug report on this repo, linking to the bug that you posted on the main CBMC repo.
