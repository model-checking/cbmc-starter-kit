# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Methods of manipulating the templates repository."""

from pathlib import Path
import importlib.util

from cbmc_starter_kit import repository

REPOSITORY_TEMPLATES = "template-for-repository"
PROOF_TEMPLATES = "template-for-proof"
PROOF_DIR = "proofs"
NEGATIVE_TESTS = "negative_tests"

COMMON_MAKEFILE = "Makefile.common"
TEMPLATE_DEFINES = "Makefile-template-defines"
PROJECT_DEFINES = "Makefile-project-defines"
RUN_SCRIPT = "run-cbmc-proofs.py"

################################################################

def package_root():
    """Directory containing the package."""

    # There are so many incompatible, deprecated ways of doing this
    # available in Python version 3.6 through 3.10, and the right
    # solution is in question.
    #
    # The right solution is actually
    #
    #   importlib.resources.files(__package__)
    #
    # but importlib.resources appears in 3.7 (with a backport
    # importlib_resources available before 3.7) and files itself
    # appears in 3.9
    #
    # The next solution is
    #
    #   importlib.resources.path(__package__, resource_name)
    #
    # but the resource_name must be a string and can't be a directory
    # or a path, and this deprecated after 3.9 in favor of files().
    #
    # The next solution is
    #
    #   pkgutil.get_data(__package__, resource_path)
    #
    # but this returns contents and not a path.  But, amazing, this
    # works even if the package is an egg or a zipfile!
    #
    # The next solution is
    #
    #     pkg_resources.resource_filename(__package__, resource_path)
    #
    # but pkg_resources is slow and distributed with setuptools and
    # not a standard module.

    # this gives the path to the package __init__.py
    init = importlib.util.find_spec(__package__).origin
    # this gives the path to the package directory
    return Path(init).parent

def package_repository_template_root():
    return package_root() / REPOSITORY_TEMPLATES

def package_proof_template_root():
    return package_root() / PROOF_TEMPLATES

################################################################
# Ask the user for set up information

def ask_for_project_name():
    """Ask user for project name."""

    return input("What is the project name? ").strip()

def ask_for_function_name():
    """Ask user for function name."""

    return input("What is the function name? ").strip()

def ask_for_source_file(func, cwd=None, repo=None):
    """Ask user to select path to source file defining function func."""

    cwd = Path(cwd or Path.cwd()).resolve()
    repo = Path(repo or repository.repository_root(cwd=cwd)).resolve()
    sources = repository.function_sources(func, cwd=cwd, repo=repo)
    options = sources + ["The source file is not listed here"]
    choices = [str(idx) for idx in range(len(options))]
    index = choices[-1]

    if sources:
        print(f"These source files define a function '{func}':")
        for idx, src in enumerate(options):
            print(f" {idx:3} {src}")
        index = input(
            f"Select a source file (the options are {', '.join(choices)}): "
        ).strip() or choices[-1]

    if index not in choices:
        raise UserWarning(f"{index} is not in {', '.join(choices)}")
    if index == choices[-1]:
        src = input(f"Enter path to source file defining {func}: ").strip()
    else:
        src = sources[int(index)]
    src = Path(src).expanduser().resolve()
    if not src.is_file():
        raise UserWarning(f"Source file '{src}' does not exist")

    return src

################################################################
