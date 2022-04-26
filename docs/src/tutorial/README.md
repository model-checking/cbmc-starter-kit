# CBMC starter kit tutorial

The [CBMC starter kit](https://github.com/model-checking/cbmc-starter-kit)
makes it easy to add CBMC verification to an existing software project.

In this tutorial, we show how to begin proving the memory safety of
a memory allocator that comes with the
[FreeRTOS Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel).
The kernel comes with five allocators, and we look at the simplest one.
It allocates blocks from a region of memory set aside for the heap.
It maintains a linked list of free blocks and allocates a block from
the first block in the free list that is big enough to satisfy the request.
When the block is freed, it is added back to the free list and merged with
adjacent free blocks already in the free list.
The function we want to prove memory safe is the allocator
[`pvPortMalloc`](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/portable/MemMang/heap_5.c#L155)
in the source file
[portable/MemMang/heap_5.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/portable/MemMang/heap_5.c).

This tutorial is actually a slightly cleaned-up version of the work done by two
developers who used the starter kit to begin verification of `pvPortMalloc`.
Two developers who had little more hand-on experience that the demonstration of
CBMC running on a few simple examples were able to use the starter kit
to begin verification in about ten or fifteen minutes, and were able to
breathe some real life into the proof within a few more hours.

Using the starter kit consists of five steps
* [Clone the source repository](#clone-the-source-repository)
* [Configure the repository](#configure-the-repository)
* [Configure the proof](#configure-the-proof)
* [Write the proof](#write-the-proof)
* [Run CBMC](#run-cbmc)

## Clone the source repository

The first step is to clone the FreeRTOS Kernel repository.
```
git clone https://github.com/FreeRTOS/FreeRTOS-Kernel.git kernel
cd kernel
git submodule update --init --checkout --recursive
```
The first line clones the repository into the directory `kernel`.
The remaining lines step into the directory `kernel`
and clone the kernel's submodules.

## Configure the repository

The next step is to configure the repository for CBMC verification.
```
mkdir cbmc
cd cbmc
cbmc-starter-kit-setup
```
```
What is the project name? Kernel
```
The first line create a `cbmc` directory to hold everything
related to CBMC verification.  The last line runs a setup script
to configure the repository for CBMC verification.
It examines the layout of the repository and asks for a name to use for
the CBMC verification project.  We use the project name `Kernel`.

Looking at the `cbmc` directory, we see that some infrastructure has
been installed:
```
ls
```
```
include         proofs          sources         stubs
```
We see directories for holding header files, source files, and stubs written
for the verification work.  Examples of useful stubs for a verification project
are `send` and `receive` methods for a physical communication network that
isn't being explicitly modeled.

The most important directory here is the `proofs` directory that will hold
the CBMC proofs themselves:
```
ls proofs
```
```
Makefile-project-defines        Makefile.common
Makefile-project-targets        README.md
Makefile-project-testing        run-cbmc-proofs.py
Makefile-template-defines
```
The most important files here are
* `Makefile.common`  This makefile
implements our best practices for CBMC verification:
  our best practices for building code for CBMC, our best practices
  for running CBMC, and for building a report of CBMC results in a form
  that makes it easy to debug issues found by CBMC.
* `run-cbmc-proofs.py` This python script runs all of the CBMC proofs in
  the `proofs` directory with maximal concurrency,
  and builds a dashboard of the results.
  This script is invoked by continuous integration to recheck the proofs on
  changes proposed in a pull request.

The remaining Makefiles are just hooks for describing project-specific
modifications or definitions.  For example, within `Makefile-project-defines`
you can define the `INCLUDES` variable to set the search path for the header
files needed to build the project functions being verified.

## Configure the proof

The next step is to configure CBMC verification of  the memory allocator
[`pvPortMalloc`](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/portable/MemMang/heap_5.c#L155)
in the source file
[portable/MemMang/heap_5.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/portable/MemMang/heap_5.c).
```
cd proofs
cbmc-starter-kit-setup-proof
```
```
What is the function name? pvPortMalloc
These source files define a function 'pvPortMalloc':
   0 ../../portable/ARMv8M/secure/heap/secure_heap.c
   1 ../../portable/GCC/ARM_CM23/secure/secure_heap.c
   2 ../../portable/GCC/ARM_CM33/secure/secure_heap.c
   3 ../../portable/IAR/ARM_CM23/secure/secure_heap.c
   4 ../../portable/IAR/ARM_CM33/secure/secure_heap.c
   5 ../../portable/MemMang/heap_1.c
   6 ../../portable/MemMang/heap_2.c
   7 ../../portable/MemMang/heap_3.c
   8 ../../portable/MemMang/heap_4.c
   9 ../../portable/MemMang/heap_5.c
  10 ../../portable/WizC/PIC18/port.c
  11 The source file is not listed here
Select a source file (the options are 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11): 9
```
This runs a setup script for the proof that first asks for the name
of the function being verified.  We give it the name `pvPortMalloc`.
It then examines the source code in the repository and lists all of
the source files that define a function named `pvPortMalloc`.  It lists
these files and asks us to chose the file with the implementation we
want to verify.  We choose source file number 9.

The `proofs` directory now contains a subdirectory `pvPortMalloc`
for verification of the memory allocator `pvPortMalloc`.
```
cd pvPortMalloc
ls
```
```
Makefile                cbmc-proof.txt          pvPortMalloc_harness.c
README.md               cbmc-viewer.json
```
The most important files in this directory are
* `Makefile` This is a skeleton of a Makefile to build and run the proof.
* `pvPortMalloc_harness.c` This is a skeleton of a proof harness
  for `pvPortMalloc`.

## Write the proof

### The Makefile

The Makefile is very simple.
```
HARNESS_ENTRY = harness
HARNESS_FILE = pvPortMalloc_harness

# This should be a unique identifier for this proof, and will appear on the
# Litani dashboard. It can be human-readable and contain spaces if you wish.
PROOF_UID = pvPortMalloc

DEFINES +=
INCLUDES +=

REMOVE_FUNCTION_BODY +=
UNWINDSET +=

PROOF_SOURCES += $(PROOFDIR)/$(HARNESS_FILE).c
PROJECT_SOURCES += $(SRCDIR)/portable/MemMang/heap_5.c

# If this proof is found to consume huge amounts of RAM, you can set the
# EXPENSIVE variable. With new enough versions of the proof tools, this will
# restrict the number of EXPENSIVE CBMC jobs running at once. See the
# documentation in Makefile.common under the "Job Pools" heading for details.
# EXPENSIVE = true

include ../Makefile.common
```
You can see that it identifies the the function `pvPortMalloc`, it
identifies the source file `portable/MemMang/heap_5.c`, and it includes
the `Makefile.common` describing our best practices for using CBMC.

It also gives us the option of defining `INCLUDES` to set the include path
for header files.  We do need a few header files to build `pvPortMalloc`,
so let us update the Makefile with
```
INCLUDES += -I$(PROOFDIR)
INCLUDES += -I$(SRCDIR)/include
INCLUDES += -I$(SRCDIR)/portable/ThirdParty/GCC/Posix
```

The final [`Makefile`](Makefile) is:
```
HARNESS_ENTRY = harness
HARNESS_FILE = pvPortMalloc_harness

# This should be a unique identifier for this proof, and will appear on the
# Litani dashboard. It can be human-readable and contain spaces if you wish.
PROOF_UID = pvPortMalloc

DEFINES +=
INCLUDES += -I$(PROOFDIR)
INCLUDES += -I$(SRCDIR)/include
INCLUDES += -I$(SRCDIR)/portable/ThirdParty/GCC/Posix

REMOVE_FUNCTION_BODY +=
UNWINDSET +=

PROOF_SOURCES += $(PROOFDIR)/$(HARNESS_FILE).c
PROJECT_SOURCES += $(SRCDIR)/portable/MemMang/heap_5.c

# If this proof is found to consume huge amounts of RAM, you can set the
# EXPENSIVE variable. With new enough versions of the proof tools, this will
# restrict the number of EXPENSIVE CBMC jobs running at once. See the
# documentation in Makefile.common under the "Job Pools" heading for details.
# EXPENSIVE = true

include ../Makefile.common
```

### The proof harness

The proof harness is also very simple (especially after omitting some
comments at the top of the file).
```
/**
 * @file pvPortMalloc_harness.c
 * @brief Implements the proof harness for pvPortMalloc function.
 */

void harness()
{

  /* Insert argument declarations */

  pvPortMalloc( /* Insert arguments */ );
}
```

We need to add the main header file `FreeRTOS.h` for the FreeRTOS project,
and we need to add a function prototype for `pvPortMalloc` saying that it
takes a size and returns a pointer.
```
#include <stdlib.h>
#include "FreeRTOS.h"
void *pvPortMalloc(size_t size);
```

All that is left is to declare an unconstrained size of type `size_t` and
pass it to `pvPortMalloc.`
```
size_t size;
pvPortMalloc(size);
```

The final [`pvPortMalloc_harness.c`](pvPortMalloc_harness.c) is:
```
/**
 * @file pvPortMalloc_harness.c
 * @brief Implements the proof harness for pvPortMalloc function.
 */

#include <stdlib.h>
#include "FreeRTOS.h"
void *pvPortMalloc(size_t size);

void harness()
{
  size_t size;
  pvPortMalloc(size);
}
```

And that is it, with the exception of one last detail.  Building FreeRTOS
requires a configuration file that sets all the parameters used to define
a system configuration.  This kernel repository does not contain a
configuration file, so let us use a simplified
configuration file from a demonstration in another repository.  Let us add
[`FreeRTOSConfig.h`](FreeRTOSConfig.h) to the `pvPortMalloc` directory.

## Run the proof

Finally, we can run the proof:
```
make
```
This builds a report of the results that we can open in a browser
```
open report/html/index.html
```
Examining [the report](report/index.html), we see a list of coverage results, a list of
warnings, and a list of errors or issues found by CBMC.  In this report,
there are no errors, but the coverage is *terrible*: only 40% of the lines
in the function are exercised by CBMC!

Further thought makes it clear that we haven't set up the heap
that the allocator is supposed to be using.  We have invoked
an allocator to allocate space on a heap, but we haven't allocated
or initialized the heap itself yet!

At this point it is interesting to see what the developers
did to breathe some life into this verification effort.
Their proof harness looked something like this
[`pvPortMalloc_harness.c`](pvPortMalloc_harness1.c):
```
/**
 * @file pvPortMalloc_harness.c
 * @brief Implements the proof harness for pvPortMalloc function.
 */

#include <stdlib.h>
#include "FreeRTOS.h"
void * pvPortMalloc( size_t xWantedSize );

void harness()
{
  /* allocate heap */
  uint8_t app_heap[ configTOTAL_HEAP_SIZE ];

  /* initialize heap */
  HeapRegion_t xHeapRegions[] =
    {
      { ( unsigned char * ) app_heap, sizeof( app_heap ) },
      { NULL,                         0                  }
    };
  vPortDefineHeapRegions( xHeapRegions );

  /* mess up heap */
  size_t xWantedSize1, xWantedSize2, xWantedSize3;
  void* pv1 = pvPortMalloc( xWantedSize1 );
  void* pv2 = pvPortMalloc( xWantedSize2 );
  void* pv3 = pvPortMalloc( xWantedSize3 );
  vPortFree( pv2 );

  size_t xWantedSize;
  pvPortMalloc( xWantedSize );
}
```
You can see that they allocate the heap, they initialize the heap
data structures, and then they mess up the heap a bit by allocating
three chunks of unconstrained size and freeing the middle one.
Then they invoke `pvPortMalloc` with an unconstrained size.
Doing this was enough to get complete code coverage and uncover a
few minor instances of integer overflow.

Of course, this is not a complete proof of memory safety.  This is a proof that
if you allocate a heap consisting of a single chunk of memory of a size
fixed by the configuration, and if you allocate three chunks of unconstrained
size and free the middle one, then `pvPortMalloc` will exhibit no memory
safety errors or other undefined behaviors.  But it is an elegant example
of how quickly developers were able to get started doing real work.
Good for them!  And, soon, good for you.
