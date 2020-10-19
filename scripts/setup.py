#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Set up the CBMC proof instrastructure."""

import logging
import os

import util

def create_makefile_template_defines(source_root, proof_root, litani):
    """Create Makefile-template-defines in the proof root."""

    makefile = os.path.join(proof_root, "Makefile-template-defines")
    if os.path.exists(makefile):
        logging.warning("Overwriting %s", makefile)

    with open(makefile, "w") as fileobj:
        print("SRCDIR ?= $(abspath $(PROOF_ROOT)/{})"
              .format(os.path.relpath(source_root, proof_root)),
              file=fileobj)
        print("LITANI ?= $(abspath $(PROOF_ROOT)/{})".format(
            os.path.relpath(source_root, litani)), file=fileobj)

def main():
    """Set up the CBMC proof infrastructure."""

    logging.basicConfig(format='%(levelname)s: %(message)s')

    source_root = util.read_source_root_path()
    cbmc_root = os.path.abspath('.')
    proof_root = util.read_proof_root_path()
    litani = util.read_litani_path()

    util.copy_repository_templates(cbmc_root)
    create_makefile_template_defines(
        source_root, proof_root, litani)

if __name__ == "__main__":
    main()
