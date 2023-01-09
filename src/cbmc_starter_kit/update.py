#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

'Update CBMC starter kit.'

from pathlib import Path
import logging
import platform
import re
import shutil

from cbmc_starter_kit import arguments, repository, util, version

################################################################

def parse_arguments():
    desc = 'Update CBMC starter kit in a CBMC proof repository.'
    options = [
        {'flag': '--cbmc-root',
         'type': Path,
         'metavar': 'CBMC',
         'help': 'Root of CBMC proof infrastructure (default: ".")'},
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
          Normally update these files with the versions in the starter kit package."""}
    ]
    args = arguments.create_parser(
        options=options,
        description=desc).parse_args()
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

################################################################

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

def remove_negative_tests(cbmc_root):
    logging.debug('Removing CBMC starter kit negative tests')
    negative_tests = cbmc_root / util.NEGATIVE_TESTS
    if negative_tests.is_dir():
        logging.info('Removing: %s', negative_tests)
        shutil.rmtree(negative_tests)

def update(cbmc_root, quiet=False):
    logging.debug('Updating CBMC starter kit')
    for path in [util.COMMON_MAKEFILE, util.RUN_SCRIPT, util.LIB_MODULE]:
        src = util.package_repository_template_root() / util.PROOF_DIR / path
        dst = cbmc_root / util.PROOF_DIR / path
        (logging.debug if quiet else logging.info)('Copying: %s -> %s', src, dst)
        assert src.exists()
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            version.copy_with_version(src, dst)

def check_for_litani(cbmc_root):
    if shutil.which('litani'):
        for fyle in (util.TEMPLATE_DEFINES, util.PROJECT_DEFINES):
            update_litani_makefile_variable(cbmc_root, Path(util.PROOF_DIR) / fyle)
        return
    logging.debug("Found litani command is not installed")
    system = platform.system()
    if system == "Darwin":
        logging.warning("Consider installing the litani command available via "
                        "'brew install litani'")
    if system == "Linux":
        logging.warning("Consider installing the litani command available via "
                        "'apt install litani*.deb'")
        logging.warning("Download the litani Debian package from "
                        "https://github.com/awslabs/aws-build-accumulator/releases/latest")
    return

def check_for_proof_ci_workflow():
    workflow_root = repository.github_actions_workflows_root()
    path_to_workflow_in_customer_repo = workflow_root / "proof_ci.yaml"
    if path_to_workflow_in_customer_repo.exists():
        version.update_existing_version_in_workflow_file(
            path_to_workflow_in_customer_repo)

################################################################

def main():
    """Update files, that were previously added, during installation of the
    CBMC starter kit package."""

    args = parse_arguments()
    logging.debug('args: %s', args)

    args = validate_cbmc_root(args)

    if not args.no_test_removal:
        remove_negative_tests(args.cbmc_root)
    if not args.no_update:
        update(args.cbmc_root)
    check_for_litani(args.cbmc_root)
    check_for_proof_ci_workflow()


################################################################

if __name__ == '__main__':
    main()
