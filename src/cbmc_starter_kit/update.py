#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

'Update CBMC starter kit.'

from pathlib import Path
import logging
import shutil
import subprocess

import git

from cbmc_starter_kit import arguments
from cbmc_starter_kit import repository
from cbmc_starter_kit import util

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
         'help': 'Root of CBMC starter kit submodule if it exists (default: installed submodule)'},
        {'flag': '--no-migrate',
         'action': 'store_true',
         'help': """
          Do not remove symlinks under CBMC_ROOT.
          Normally remove symlinks under CBMC_ROOT to files under STARTER_KIT_ROOT."""},
        {'flag': '--no-test-removal',
         'action': 'store_true',
         'help': """
          Do not remove negative tests in CBMC_ROOT/negative_tests.
          Normally remove the directory CBMC_ROOT/negative_tests since most projects don't
          use these tests."""},
        {'flag': '--no-update',
         'action': 'store_true',
         'help': """
          Do not update Makefile.common and run-cbmc-proofs.py under CBMC_ROOT/proofs.
          Normally update these files with copies in this version of the current starter kit."""},
        {'flag': '--no-starter-kit-removal',
         'action': 'store_true',
         'help': """
          Do not try to remove the CBMC starter kit submodule.
          Normally check for existence of submodule but remove only with --force."""},
        {'flag': '--force',
         'action': 'store_true',
         'help': """
          Remove the CBMC starter kit submodule if it exists.
          This positive confirmation is a safety check that is required before removing
          any repository submodules."""},
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
    if not (args.cbmc_root/'proofs').is_dir():
        raise UserWarning(f'CBMC root is missing a proofs subdirectory: {args.cbmc_root}')
    logging.debug('CBMC root: %s', args.cbmc_root)
    return args

def validate_starter_kit_root(args):
    starter_kit = repository.starter_kit_root(repo=args.cbmc_root, abspath=True)
    args.starter_kit_root = args.starter_kit_root or starter_kit
    if args.starter_kit_root:
        args.starter_kit_root = args.starter_kit_root.resolve()
        if not args.starter_kit_root.is_dir():
            raise UserWarning(f'Starter kit root is not a directory: {args.starter_kit_root}')
        if not (args.starter_kit_root/'template-for-repository').is_dir():
            raise UserWarning('Starter kit root is missing a template-for-repository subdirectory:'
                              f' {args.starter_kit_root}')
        if not args.starter_kit_root.is_relative_to(args.cbmc_root):
            raise UserWarning(f'Starter kit root is {args.starter_kit_root} is not a descendant of '
                              f'CBMC root {args.cbmc_root}')
    else:
        args.no_migrate = True
    logging.debug('CBMC starter kit root: %s', args.starter_kit_root)
    return args

################################################################

def files_under_root(root=None, symlinks_only=False):
    cmd = ['find', '.']
    if symlinks_only:
        cmd += ['-type', 'l']
    kwds = {
        'cwd': root,
        'text': True,
        'capture_output': True,
    }
    files = subprocess.run(cmd, **kwds, check=True).stdout.splitlines()
    return sorted(files)

################################################################

def migrate(cbmc_root, starter_kit_root):
    logging.debug('Migrating CBMC starter kit')
    templates = files_under_root(starter_kit_root/'template-for-repository')
    logging.debug('Migrating CBMC starter kit: found templates: %s', templates)
    symlinks = files_under_root(cbmc_root, symlinks_only=True)
    logging.debug('Migrating CBMC starter kit: found symlinks: %s', symlinks)

    cbmc_symlinks = [path for path in templates if path in symlinks]
    for symlink in cbmc_symlinks:
        cbmc_link = cbmc_root / symlink
        cbmc_file = cbmc_link.resolve()
        logging.warning('Copying: %s -> %s', cbmc_file, cbmc_link)
        assert cbmc_file.exists()
        assert cbmc_link.exists()
        cbmc_link.unlink()
        shutil.copy(cbmc_file, cbmc_link)

def remove_negative_tests(cbmc_root):
    logging.debug('Removing CBMC starter kit negative tests')
    negative_tests = cbmc_root / 'negative_tests'
    if negative_tests.is_dir():
        logging.warning('Removing: %s', negative_tests)
        shutil.rmtree(negative_tests)

def update(cbmc_root):
    logging.debug('Updating CBMC starter kit')
    for path in ['proofs/Makefile.common', 'proofs/run-cbmc-proofs.py']:
        src = util.repository_template_root() / path
        dst = cbmc_root / path
        logging.warning('Copying: %s -> %s', src, dst)
        shutil.copy(src, dst)

def remove_starter_kit_submodule(cbmc_root, force=False):
    logging.debug('Checking for starter kit submodule')
    starter_kit = repository.starter_kit_root(repo=cbmc_root, abspath=False)
    if not starter_kit:
        logging.debug('Starter kit submodule does not exist')
        return
    if not force:
        logging.warning('Use --force if you want to remove the starter kit submodule: %s',
                        starter_kit)
        return
    for submodule in git.Repo(cbmc_root, search_parent_directories=True).submodules:
        if submodule.path == str(starter_kit):
            logging.warning('Removing: starter kit submodule: %s', starter_kit)
            submodule.remove()
            return
    logging.error('This should be impossible: Failed to remove starter kit submodule: %s',
                  starter_kit)

################################################################

def main():
    """Migrate CBMC starter kit from submodule to pip package."""

    args = parse_arguments()
    logging.debug('args: %s', args)

    args = validate_cbmc_root(args)
    args = validate_starter_kit_root(args)

    if not args.no_migrate:
        migrate(args.cbmc_root, args.starter_kit_root)
    if not args.no_test_removal:
        remove_negative_tests(args.cbmc_root)
    if not args.no_update:
        update(args.cbmc_root)
    if not args.no_starter_kit_removal:
        remove_starter_kit_submodule(args.cbmc_root, args.force)

################################################################

if __name__ == '__main__':
    main()
