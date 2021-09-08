#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the CBMC proof instrastructure."""

import logging
import os

import util

SRCDIR_TEXT = """
# Absolute path to the root of the source tree.
#
SRCDIR ?= $(abspath $(PROOF_ROOT)/{})
"""

LITANI_TEXT = """
# Absolute path to the litani script.
#
LITANI ?= $(abspath $(PROOF_ROOT)/{})
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

    with open(makefile, "w") as fileobj:
        print(SRCDIR_TEXT.format(os.path.relpath(source_root, proof_root)),
              file=fileobj)
        print(LITANI_TEXT.format(os.path.relpath(litani, proof_root)),
              file=fileobj)
        print(PROJECT_TEXT.format(project_name), file=fileobj)

def main():
    """Set up the CBMC proof infrastructure."""

    logging.basicConfig(format='%(levelname)s: %(message)s')

    source_root = util.read_source_root_path()

    # the script is being run in the cbmc root
    cbmc_root = os.path.abspath('.')

    # the script is creating the proof root
    proof_root = os.path.abspath('proofs')

    # the script is linking to the litani script within the litani submodule
    litani = util.read_litani_path()

    # the name of the project used in project verification reports
    project_name = util.read_project_name()

    util.copy_repository_templates(cbmc_root)
    create_makefile_template_defines(
        proof_root, source_root, litani, project_name)

if __name__ == "__main__":
    main()
