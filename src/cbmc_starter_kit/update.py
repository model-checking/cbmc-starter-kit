#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

'Update CBMC starter kit.'

from pathlib import Path
import logging
import platform
import re
import shutil
import subprocess
import sys

import git

from cbmc_starter_kit import arguments
from cbmc_starter_kit import repository
from cbmc_starter_kit import util
from cbmc_starter_kit import version

################################################################

def parse_arguments():
    desc = 'Update CBMC starter kit in a CBMC proof repository.'
    options = [
        {'flag': '--cbmc-root',
         'type': Path,
         'metavar': 'CBMC',
         'help': 'Root of CBMC proof infrastructure (default: ".")'},
        {'flag': '--starter-kit-root',
         'type': Path,
         'metavar': 'STARTER_KIT',
         'help': """
          Root of CBMC starter kit submodule (default: None or root of starter kit submodule
          installed in repository containing CBMC)"""},
        {'flag': '--no-migrate',
         'action': 'store_true',
         'help': """
          Do not remove symlinks under CBMC.
          Normally remove symlinks under CBMC to files under STARTER_KIT."""},
        {'flag': '--no-test-removal',
         'action': 'store_true',
         'help': """
          Do not remove negative tests in CBMC/negative_tests.
          Normally remove the directory CBMC/negative_tests since most projects don't
          use these tests."""},
        {'flag': '--no-update',
         'action': 'store_true',
         'help': """
          Do not update Makefile.common and run-cbmc-proofs.py under CBMC/proofs.
          Normally update these files with the versions in the starter kit package."""},
        {'flag': '--remove-starter-kit-submodule',
         'action': 'store_true',
         'help': """
          Remove the starter kit submodule if it is present.
          Normally just recommend removal."""},
        {'flag': '--remove-litani-submodule',
         'action': 'store_true',
         'help': """
          Remove the litani submodule and update the definition of LITANI in
          Makefile-template-defines if the litani submodule is present and
          the litani command is in PATH.
          Normally just recommend removal."""},
    ]
    args = arguments.create_parser(options, desc).parse_args()
    arguments.configure_logging(args)
    return args

################################################################

def validate_cbmc_root(args):
    args.cbmc_root = args.cbmc_root or Path('.')
    args.cbmc_root = args.cbmc_root.resolve()
    if not args.cbmc_root.is_dir():
        raise UserWarning(f'CBMC root is not a directory: {args.cbmc_root}')
    if not (args.cbmc_root/util.PROOF_DIR).is_dir():
        raise UserWarning(f'CBMC root is missing a {util.PROOF_DIR} subdirectory: {args.cbmc_root}')
    logging.debug('CBMC root: %s', args.cbmc_root)
    return args

def validate_starter_kit_root(args):
    starter_kit = repository.starter_kit_root(repo=args.cbmc_root, abspath=True)
    args.starter_kit_root = args.starter_kit_root or starter_kit
    if args.starter_kit_root:
        args.starter_kit_root = args.starter_kit_root.resolve()
        if not args.starter_kit_root.is_dir():
            raise UserWarning(f'Starter kit root is not a directory: {args.starter_kit_root}')
        if not (args.starter_kit_root/util.REPOSITORY_TEMPLATES).is_dir():
            raise UserWarning(f'Starter kit root is missing a {util.REPOSITORY_TEMPLATES} '
                              f'subdirectory: {args.starter_kit_root}')
        if args.cbmc_root not in args.starter_kit_root.parents:
            raise UserWarning(f'Starter kit root is {args.starter_kit_root} is not a descendant of '
                              f'CBMC root {args.cbmc_root}')
    else:
        args.no_migrate = True
    logging.debug('CBMC starter kit root: %s', args.starter_kit_root)
    return args

################################################################

def files_under_root(root=None, symlinks_only=False):
    if root and not root.is_dir():
        logging.critical('Not a directory: %s', root)
        sys.exit(1)

    cmd = ['find', '.']
    if symlinks_only:
        cmd += ['-type', 'l']
    kwds = {
        'cwd': root,
        'text': True,
        'capture_output': True,
    }
    result = subprocess.run(cmd, **kwds, check=True)

    if not result.returncode:
        return sorted(result.stdout.splitlines())
    logging.critical('This should be impossible: Failed to list files under directory: %s', root)
    sys.exit(1)

################################################################

def remove_submodule(cbmc_root, submodule_name, submodule_path):
    """Remove the submodule at the named path in the repository"""

    for submodule in git.Repo(cbmc_root, search_parent_directories=True).submodules:
        if submodule.path == str(submodule_path):
            logging.info('Removing: %s submodule: %s', submodule_name, submodule_path)
            try:
                submodule.remove()
            except git.InvalidGitRepositoryError as error:
                # remove uses git cherry to compare working branches with upstream branches
                # and throws InvalidGitRepositoryError if it finds an inconsistency.
                logging.debug(error)
                logging.error('Unable to remove %s submodule: %s',  submodule_name, submodule_path)
                logging.error('Try again after running "git fetch" in %s', submodule_path)
            return
    logging.error("Failed to remove %s submodule: %s", submodule_name, submodule_path)

def update_litani_makefile_variable(cbmc_root, path):
    """Update LITANI to LITANI?=litani in the makefile at the named path"""

    is_litani_line = lambda line: bool(re.match(r'^\s*LITANI\s*\??=', line))

    with open(cbmc_root/path, encoding='utf-8') as makefile:
        lines = makefile.read().splitlines()
    if not any(is_litani_line(line) for line in lines):
        logging.debug("Not updating LITANI in makefile: %s", path)
        return

    logging.info("Updating LITANI in makefile: %s", path)
    with open(cbmc_root/path, 'w', encoding='utf-8') as makefile:
        for line in lines:
            if is_litani_line(line):
                line = 'LITANI ?= litani'
            print(line, file=makefile)
    return

################################################################

def migrate(cbmc_root, starter_kit_root):
    logging.debug('Migrating CBMC starter kit')
    templates = files_under_root(starter_kit_root/util.REPOSITORY_TEMPLATES)
    logging.debug('Migrating CBMC starter kit: found templates: %s', templates)
    symlinks = files_under_root(cbmc_root, symlinks_only=True)
    logging.debug('Migrating CBMC starter kit: found symlinks: %s', symlinks)

    cbmc_symlinks = [path for path in templates if path in symlinks]
    for symlink in cbmc_symlinks:
        cbmc_link = cbmc_root / symlink
        cbmc_file = cbmc_link.resolve()
        logging.info('Copying: %s -> %s', cbmc_file, cbmc_link)
        assert cbmc_file.exists()
        assert cbmc_link.exists()
        cbmc_link.unlink()
        shutil.copy(cbmc_file, cbmc_link)

def remove_negative_tests(cbmc_root):
    logging.debug('Removing CBMC starter kit negative tests')
    negative_tests = cbmc_root / util.NEGATIVE_TESTS
    if negative_tests.is_dir():
        logging.info('Removing: %s', negative_tests)
        shutil.rmtree(negative_tests)

def update(cbmc_root, quiet=False):
    logging.debug('Updating CBMC starter kit')
    for path in [f'{util.PROOF_DIR}/{util.COMMON_MAKEFILE}', f'{util.PROOF_DIR}/{util.RUN_SCRIPT}']:
        src = util.package_repository_template_root() / path
        dst = cbmc_root / path
        (logging.debug if quiet else logging.info)('Copying: %s -> %s', src, dst)
        version.copy_with_version(src, dst)

def check_for_starter_kit_submodule(cbmc_root, remove=False):
    starter_path = repository.starter_kit_root(repo=cbmc_root, abspath=False)
    if not starter_path:
        logging.debug("Found starter kit submodule is not installed")
        return

    if not remove:
        logging.warning("Consider using --remove-starter-kit-submodule to remove the starter kit "
                        "submodule")
        return

    remove_submodule(cbmc_root, "starter kit", starter_path)

def check_for_litani_submodule(cbmc_root, remove=False):
    litani_path = repository.litani_root(repo=cbmc_root, abspath=False)
    if not litani_path:
        logging.debug("Found litani submodule is not installed")
        return

    litani_command = shutil.which('litani')
    if not litani_command:
        logging.debug("Found litani command is not installed")
        system = platform.system()
        if system == "Darwin":
            logging.warning("Consider replacing the litani submodule with the litani command "
                            "available via 'brew install litani'")
        if system == "Linux":
            logging.warning("Consider replacing the litani submodule with the litani command "
                            "available via 'apt install litani*.deb'")
            logging.warning("Download the litani package litani*.deb from the release page "
                            "https://github.com/awslabs/aws-build-accumulator/releases/latest")
        return

    if not remove:
        logging.warning("Consider using --remove-litani-submodule to remove the litani submodule "
                        "and update makefiles to use the litani command")
        return

    remove_submodule(cbmc_root, "litani", litani_path)
    update_litani_makefile_variable(cbmc_root, Path(util.PROOF_DIR)/util.TEMPLATE_DEFINES)
    update_litani_makefile_variable(cbmc_root, Path(util.PROOF_DIR)/util.PROJECT_DEFINES)

################################################################

def main():
    """Migrate CBMC starter kit from submodule to pip package."""

    args = parse_arguments()
    logging.debug('args: %s', args)

    try:
        args = validate_cbmc_root(args)
        args = validate_starter_kit_root(args)

        if not args.no_migrate:
            migrate(args.cbmc_root, args.starter_kit_root)
        if not args.no_test_removal:
            remove_negative_tests(args.cbmc_root)
        if not args.no_update:
            update(args.cbmc_root)
        check_for_starter_kit_submodule(args.cbmc_root, args.remove_starter_kit_submodule)
        check_for_litani_submodule(args.cbmc_root, args.remove_litani_submodule)
    except UserWarning:
        starter_kit = repository.starter_kit_root(repo=args.cbmc_root)
        if starter_kit and (starter_kit / "setup.cfg").exists():
            logging.error("The starter kit submodule is at a version >1.0: %s", starter_kit)
            logging.error("Consider backing up to version 1.0 with the following commands")
            logging.error("  pushd %s", starter_kit)
            logging.error("  git fetch --tags")
            logging.error("  git checkout starterkit-1.0")
            logging.error("  popd")
            logging.error("and running cbmc-starter-kit-update again with --remove-starter-kit.")
        raise

################################################################

if __name__ == '__main__':
    main()
