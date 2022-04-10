#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up a CBMC proof."""

from pathlib import Path
import os
import shutil

from cbmc_starter_kit import arguments
from cbmc_starter_kit import repository
from cbmc_starter_kit import util

################################################################

def parse_arguments():
    desc = "Set up CBMC proof infrastructure for a proof."
    options = []
    args = arguments.create_parser(options, desc).parse_args()
    arguments.configure_logging(args)
    return args

################################################################

def proof_template_filenames():
    for path in util.package_proof_template_root().iterdir():
        yield path

def read_proof_template(path):
    with open(path, encoding='utf-8') as data:
        return data.read().splitlines()

def write_proof_template(lines, filename, directory):
    with open(directory / filename, "w", encoding='utf-8') as data:
        data.write('\n'.join(lines) + '\n')

def rename_proof_harness(function, directory):
    shutil.move(directory / "FUNCTION_harness.c", directory / f"{function}_harness.c")

################################################################

def patch_function_name(lines, function):
    return [line.replace("<__FUNCTION_NAME__>", function) for line in lines]

def patch_path_to_makefile(lines, proof_root, proof_dir):
    path = os.path.relpath(proof_root, proof_dir)
    return [line.replace("<__PATH_TO_MAKEFILE__>", path) for line in lines]

def patch_path_to_proof_root(lines, proof_root, source_root):
    path = os.path.relpath(proof_root, source_root)
    return [line.replace("<__PATH_TO_PROOF_ROOT__>", path) for line in lines]

def patch_path_to_source_file(lines, source_file, source_root):
    path = os.path.relpath(source_file, source_root)
    return [line.replace("<__PATH_TO_SOURCE_FILE__>", path) for line in lines]

################################################################

def main():
    """Set up CBMC proof."""

    parse_arguments() # only arguments are --verbose and --debug

    function = util.ask_for_function_name()
    source_file = util.ask_for_source_file(function)
    source_root = repository.repository_root()
    proof_root = repository.proofs_root()


    proof_dir = Path(function)
    proof_dir.mkdir()

    for filename in proof_template_filenames():
        lines = read_proof_template(filename)
        lines = patch_function_name(lines, function)
        lines = patch_path_to_makefile(lines, proof_root, proof_dir)
        lines = patch_path_to_proof_root(lines, proof_root, source_root)
        lines = patch_path_to_source_file(lines, source_file, source_root)
        write_proof_template(lines, filename.name, proof_dir)

    rename_proof_harness(function, proof_dir)

if __name__ == "__main__":
    main()
