#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys

################################################################
# Command line arguments

def create_parser(desc, args, epilog=None):
    default_args = [
        {
            "flag": "--verbose",
            "action": "store_true",
            "help": "Verbose output"
        },
        {
            "flag": "--debug",
            "action": "store_true",
            "help": "Debug output"
        }
    ]
    args.extend(default_args)

    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    for arg in args:
        flag = arg.pop('flag')
        parser.add_argument(flag, **arg)
    return parser

def parser():
    desc = "Remove Apache references from files copied from the CBMC starter kit"
    args = [
        {
            "flag": "--proofdir",
            "help": "Root of the proof subtree (default: %(default)s)",
            "default": ".",
        },
        {
            "flag": "--remove",
            "action": "store_true",
            "help": "Remove Apache references from files under PROOFDIR (otherwise just list them)"
        },
    ]
    epilog = """
    The CBMC starter kit was originally released under the Apache
    license. All files in the starter kit contained references to the
    Apache license. The starter kit installation scripts copied files
    from the stater kit into the project repository.  This became an
    issue when the project repository was released under a different
    license.  This script removes all references to the Apache license
    from the files copied into the project repository from the starter
    kit.
    """

    return create_parser(desc, args, epilog)

def configure_logging(args):
    # Logging is configured by the first invocation of logging.basicConfig
    fmt = '%(levelname)s: %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=fmt)
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format=fmt)
    logging.basicConfig(format=fmt)

################################################################
# Shell out commands

def run(cmd, cwd=None, encoding=None):
    """Run a command in a subshell and return the standard output.

    Run the command cmd in the directory cwd and use encoding to
    decode the standard output.
    """

    kwds = {
        'cwd': cwd,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'text': True,
    }
    if sys.version_info >= (3, 6): # encoding introduced in Python 3.6
        kwds['encoding'] = encoding

    logging.debug('Running "%s" in %s', ' '.join(cmd), cwd)

    result = subprocess.run(cmd, **kwds, check=False)
    if result.returncode:
        logging.debug('Failed command: %s', ' '.join(cmd))
        logging.debug('Failed return code: %s', result.returncode)
        logging.debug('Failed stdout: %s', result.stdout.strip())
        logging.debug('Failed stderr: %s', result.stderr.strip())
        return []

    # Remove line continuations before splitting stdout into lines
    # Running command with text=True converts line endings to \n in stdout
    lines = result.stdout.replace('\\\n', ' ').splitlines()
    return [strip_whitespace(line) for line in lines]

def strip_whitespace(string):
    return re.sub(r'\s+', ' ', string).strip()

################################################################

def maybe_a_copied_file(path):
    copied_files = [
        'Makefile',
        'Makefile-project-defines',
        'Makefile-project-targets',
        'Makefile-project-testing',
    ]
    return os.path.basename(path) in copied_files

def find_apache_references(proofdir=None):
    paths = run(['git', 'grep', '-l', 'Apache', '.'], cwd=proofdir)
    paths = [os.path.normpath(os.path.join(proofdir, path)) for path in paths]
    paths = [path for path in paths if not os.path.islink(path)]
    return sorted(paths)

def remove_apache_reference(path, extension='backup'):
    apache_references = [
        '# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.',
        '# SPDX-License-Identifier: Apache-2.0'
    ]
    backup = path + '.' + extension
    shutil.move(path, backup)
    with open(backup) as infile, open(path, "w") as outfile:
        removed = False
        for line in infile:
            if strip_whitespace(line) in apache_references:
                removed = True
                logging.debug('Deleted Apache reference in %s: %s',
                             path, strip_whitespace(line))
                continue
            outfile.write(line)
        if removed:
            logging.info('Deleted Apache reference in %s', path)
            return True
        return False

def remove_apache_references(paths):
    removed = False
    for path in paths:
        if not maybe_a_copied_file(path):
            logging.debug('Skipping %s', path)
            continue
        logging.debug('Updating %s', path)
        removed = remove_apache_reference(path) or removed
    return removed

################################################################

def main():
    args = parser().parse_args()
    configure_logging(args)

    paths = find_apache_references(args.proofdir)

    if not args.remove:
        if paths:
            print("The following files contain references to the Apache license:")
            for path in paths:
                print(f"  {path}")
            script = os.path.basename(sys.argv[0])
            print(f"Remove Apache references from these files with '{script} --remove'")
        exit(0)

    remove_apache_references(paths)

    paths = find_apache_references(args.proofdir)
    if paths:
        logging.warning("Files left unchanged contain Apache references: %s", ', '.join(paths))
        exit(1)

    exit(0)

if __name__ == "__main__":
    main()
