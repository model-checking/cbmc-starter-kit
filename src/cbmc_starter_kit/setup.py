#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the CBMC proof instrastructure."""

from pathlib import Path
import os
import shutil

from cbmc_starter_kit import arguments
from cbmc_starter_kit import repository
from cbmc_starter_kit import update
from cbmc_starter_kit import util

################################################################

def parse_arguments():
    desc = "Set up CBMC proof infrastructure for a repository."
    options = []
    args = arguments.create_parser(options, desc).parse_args()
    arguments.configure_logging(args)
    return args

################################################################

SRCDIR_TEXT = """
# Absolute path to the root of the source tree.
#
SRCDIR ?= {}
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
#         make PROJECT_NAME="FreeRTOS MQTT" report
#
PROJECT_NAME = "{}"
"""

def srcdir_definition(source_root, proof_root):
    # Let makefile construct absolute path to source root
    srcdir_path = f"$(abspath $(PROOF_ROOT)/{os.path.relpath(source_root, proof_root)})"
    return SRCDIR_TEXT.format(srcdir_path)

def litani_definition(litani, proof_root):
    if litani.is_file():
        # Let makefile construct absolute path to litani
        litani_path = f"$(abspath $(PROOF_ROOT)/{os.path.relpath(litani, proof_root)})"
        return LITANI_TEXT.format(litani_path)
    return LITANI_TEXT.format(litani)

def project_name_definition(project_name):
    return PROJECT_TEXT.format(project_name)

################################################################

def main():
    """Set up the CBMC proof infrastructure."""

    parse_arguments() # only arguments are --verbose and --debug

    # Gather project-specific definitions
    source_root = repository.repository_root()
    if shutil.which("litani"):
        litani = Path("litani")
    else:
        litani = repository.litani_root() / "litani"
    project_name = util.ask_for_project_name()

    # Copy cbmc infrastructure into cbmc directory
    cbmc_root = Path.cwd()
    shutil.copytree(util.package_repository_template_root(), cbmc_root, dirs_exist_ok=True)
    shutil.rmtree(cbmc_root / util.NEGATIVE_TESTS, ignore_errors=True)
    shutil.rmtree(cbmc_root / util.PROOF_DIR / "__pycache__", ignore_errors=True)

    # Overwrite Makefile.common and run-cbmc-proofs.py with versioned copies
    # Quiet warnings about overwriting files
    update.update(cbmc_root, quiet=True)

    # Write project-specific definitions to cbmc/proofs/Makefile-template-defines
    proof_root = cbmc_root / util.PROOF_DIR
    makefile = proof_root/util.TEMPLATE_DEFINES
    with open(makefile, "w", encoding='utf-8') as mkfile:
        print(srcdir_definition(source_root, proof_root), file=mkfile)
        print(litani_definition(litani, proof_root), file=mkfile)
        print(project_name_definition(project_name), file=mkfile)

if __name__ == "__main__":
    main()
