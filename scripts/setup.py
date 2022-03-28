#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the CBMC proof instrastructure."""

from pathlib import Path
import logging
import os
import shutil

import repository
import util

SRCDIR_TEXT = """
# Absolute path to the root of the source tree.
#
SRCDIR ?= $(abspath $(PROOF_ROOT)/{})
"""

LITANI_TEXT = """
# Absolute path to the litani script.
#
LITANI ?= {}
"""

PROJECT_TEXT = """
# Name of this proof project, displayed in proof reports. For example,
# "s2n" or "Amazon FreeRTOS". For projects with multiple proof roots,
# this may be overridden on the command-line to Make, for example
#
# 	  make PROJECT_NAME="FreeRTOS MQTT" report
#
PROJECT_NAME = "{}"
"""

def create_makefile_template_defines(
        proof_root, source_root, litani, project_name):
    """Create Makefile-template-defines in the proof root."""

    makefile = os.path.join(proof_root, "Makefile-template-defines")
    if os.path.exists(makefile):
        logging.warning("Overwriting %s", makefile)

    with open(makefile, "w", encoding='utf-8') as fileobj:
        print(SRCDIR_TEXT.format(os.path.relpath(source_root, proof_root)),
              file=fileobj)
        print(LITANI_TEXT.format(litani), file=fileobj)
        print(PROJECT_TEXT.format(project_name), file=fileobj)

def main():
    """Set up the CBMC proof infrastructure."""

    logging.basicConfig(format='%(levelname)s: %(message)s')

    cbmc_root = Path.cwd()
    proof_root = cbmc_root / "proofs"
    source_root = repository.repository_root()
    litani = "litani" if shutil.which("litani") else \
        repository.litani_root() / "litani"
    if litani != "litani":
        relpath_from_litani_to_proof_root = os.path.relpath(litani, proof_root)
        litani = f"$(abspath $(PROOF_ROOT)/{relpath_from_litani_to_proof_root})"
    project_name = util.ask_for_project_name()

    util.copy_repository_templates(cbmc_root)
    create_makefile_template_defines(
        proof_root, source_root, litani, project_name
    )

if __name__ == "__main__":
    main()
