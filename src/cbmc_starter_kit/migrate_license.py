#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import os
import re
import shutil
import subprocess
import sys

from cbmc_starter_kit import arguments

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
    with open(backup, encoding='utf-8') as infile, open(path, "w", encoding='utf-8') as outfile:
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

    desc = "Remove references to Apache license from CBMC starter kit."

    options = [
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

    args = arguments.create_parser(options, desc, epilog).parse_args()
    arguments.configure_logging(args)

    paths = find_apache_references(args.proofdir)

    if not args.remove:
        if paths:
            print("The following files contain references to the Apache license:")
            for path in paths:
                print(f"  {path}")
            script = os.path.basename(sys.argv[0])
            print(f"Remove Apache references from these files with '{script} --remove'")
        sys.exit(0)

    remove_apache_references(paths)

    paths = find_apache_references(args.proofdir)
    if paths:
        logging.warning("Files left unchanged contain Apache references: %s", ', '.join(paths))
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
