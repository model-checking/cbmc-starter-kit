# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Methods of manipulating the templates repository."""

from pathlib import Path
import logging
import os
import shutil
import repository

REPOSITORY_TEMPLATES = "template-for-repository"
PROOF_TEMPLATES = "template-for-proof"

PROOF_DIR = "proofs"

# There are some files that we should copy to the project repository rather than
# symlinking. This is because users are expected to modify these files. If the
# files were symlinks, then modifying them would dirty up this submodule, which
# would prevent project owners from cleanly updating it.
COPY_INSTEAD = [
    "Makefile-project-defines",
    "Makefile-project-targets",
    "Makefile-project-testing",
    ".gitignore",
]

################################################################

def script_dir():
    """Directory containing setup scripts."""

    return os.path.dirname(os.path.abspath(__file__))

def templates_root():
    """Directory containing the AWS-templates-for-CBMC repository."""

    return os.path.dirname(script_dir())

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
    sources = repository.function_sources(func, cwd=cwd, repo=repo, abspath=False)
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
    src = Path(src)
    if not src.is_file():
        raise UserWarning(f"Source file '{src}' does not exist")

    return src

################################################################

def files_under_root(root):
    """The list of files in the filesystem under root."""

    cwd = os.getcwd()
    try:
        os.chdir(root)
        return [os.path.join(path, name)
                for path, _, files in os.walk('.') for name in files]
    finally:
        os.chdir(cwd)


def link_files(name, src, dst):
    """Link file dst/name to file src/name, return number skipped"""

    src_name = os.path.normpath(os.path.join(src, name))
    dst_name = os.path.normpath(os.path.join(dst, name))

    os.makedirs(os.path.dirname(dst_name), exist_ok=True)
    src_link = os.path.relpath(src_name, os.path.dirname(dst_name))

    if os.path.basename(name) in COPY_INSTEAD:
        install_method = ("copy", shutil.copyfile)
        src_link = src_name
    else:
        install_method = ("symlink", os.symlink)

    if os.path.exists(dst_name):
        logging.warning("Skipping %s %s -> %s: file exists",
                        install_method[0], name, src_link)
        return 1

    logging.debug(
        "Creating %s %s -> %s", install_method[0], name, src_link)
    install_method[1](src_link, dst_name)
    return 0

def copy_directory_contents(src, dst, exclude=None):
    """Link the contents of one directory into another."""

    src = os.path.normpath(src)
    dst = os.path.normpath(dst)

    assert os.path.isdir(src)
    assert os.path.isdir(dst)

    skipped = 0
    for name in files_under_root(src):
        name = os.path.normpath(name)
        if exclude and name.startswith(exclude):
            continue
        skipped += link_files(name, src, dst)

    if skipped:
        logging.warning("To overwrite a skipped file, "
                        "delete the file and rerun the script.")

def copy_repository_templates(cbmc_root):
    """Copy the files in the repository template into the CBMC root."""

    copy_directory_contents(os.path.join(templates_root(),
                                         REPOSITORY_TEMPLATES),
                            cbmc_root,
                            exclude="negative_tests")
