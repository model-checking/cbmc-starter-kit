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
