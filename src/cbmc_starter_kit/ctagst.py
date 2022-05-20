"""Ctags support for locating symbol definitions"""

from pathlib import Path
import json
import logging
import subprocess
import sys

################################################################
# This popen method is used to subprocess-out the invocation of ctags.
# This method duplicates code in other modules to make this ctags
# module a stand-alone module that can be copied and reused in other
# projects.

def popen(cmd, cwd=None, stdin=None, encoding=None):
    """Run a command with string stdin on stdin, return stdout and stderr."""

    cmd = [str(word) for word in cmd]
    kwds = {'cwd': cwd,
            'text': True,
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE}
    if sys.version_info >= (3, 6): # encoding is new in Python 3.6
        kwds['encoding'] = encoding or 'utf-8'
    try:
        logging.debug('Popen command: "%s"', ' '.join(cmd))
        logging.debug('Popen stdin: "%s"', stdin)
        with subprocess.Popen(cmd, **kwds) as pipe:
            stdout, stderr = pipe.communicate(input=stdin)
        logging.debug('Popen stdout: "%s"', stdout)
        logging.debug('Popen stderr: "%s"', stderr)
        if pipe.returncode:
            logging.debug('Popen command failed: "%s"', ' '.join(cmd))
            logging.debug('Popen return code: "%s"', pipe.returncode)
            raise UserWarning(f"Failed to run command: {' '.join(cmd)}")
        return stdout, stderr
    except FileNotFoundError as error:
        logging.debug("FileNotFoundError: command '%s': %s", ' '.join(cmd), error)
        raise UserWarning(f"Failed to run command: {' '.join(cmd)}") from error

################################################################

def ctags(root, files):
    """List symbols defined in files under root."""

    root = Path(root)
    files = [str(file_) for file_ in files]
    return (universal_ctags(root, files) or
            exhuberant_ctags(root, files) or
            legacy_ctags(root, files) or
            [])

################################################################

def universal_ctags(root, files):
    """Use universal ctags to list symbols defined in files under root."""

    # See universal ctags man page at https://docs.ctags.io/en/latest/man/ctags.1.html
    cmd = [
        'ctags',
        '-L', '-', # read files from standard input, one file per line
        '-f', '-', # write tags to standard output, one tag per line
        '--output-format=json', # each tag is a one-line json blob
        '--fields=FNnK' # json blob is {"name": symbol, "path": file, "line": line, "kind": kind}
    ]
    try:
        logging.info("Running universal ctags")
        stdout, _ = popen(cmd, cwd=root, stdin='\n'.join(files))
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Universal ctags failed")
        strings = []

    return [tag for string in strings for tag in universal_tag(root, string)]

def universal_tag(root, string):
    """Extract tag from universal ctag output."""

    try:
        # universal ctag json output is '{"name": symbol, "path": file, "line": line, "kind": kind}'
        blob = json.loads(string)
        return [{'symbol': blob['name'], 'file': root/blob['path'], 'line': int(blob['line']),
                 'kind': blob['kind']}]
    except (json.decoder.JSONDecodeError, # json is unparsable
            KeyError,                     # json key is missing
            ValueError) as error:         # invalid literal for int()
        logging.debug("Bad universal ctag: %s: %s", string, error)
        return []

################################################################

def exhuberant_ctags(root, files):
    """Use exhuberant ctags to list symbols defined in files under root."""

    # See exhuberant ctags man page at https://linux.die.net/man/1/ctags
    cmd = [
        'ctags',
        '-L', '-', # read files from standard input, one file per line
        '-f', '-', # write tags to standard output, one tag per line
        '-n', # use line numbers (not search expressions) to locate symbol in file
        '--fields=K' # include symbol kind among extension fields
    ]
    try:
        logging.info("Running exhuberant ctags")
        stdout, _ = popen(cmd, cwd=root, stdin='\n'.join(files))
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Exhuberant ctags failed")
        strings = []

    return [tag for string in strings for tag in exhuberant_tag(root, string)]

def exhuberant_tag(root, string):
    """Extract tag from exhuberant ctag output."""

    try:
        # exhuberant ctag output is 'symbol<TAB>path<TAB>line;"<TAB>kind'
        left, right = string.split(';"')[:2]
        symbol, path, line = left.split("\t")[:3]
        kind = right.split("\t")[1]
        return [{'symbol': symbol, 'file': root/path, 'line': int(line), 'kind': kind}]
    except (ValueError, IndexError): # not enough values to unpack, invalid literal for int()
        logging.debug('Bad exhuberant ctag: "%s"', string)
        return []

################################################################

def legacy_ctags(root, files):
    """Use legacy ctags to list symbols defined in files under root."""

    # MacOS ships with a legacy ctags from BSD installed in /usr/bin/ctags.
    # See the MacOS man page for the documentation used to implement this method.
    cmd = ['ctags',
           '-x',  # write human-readable summary to standard output
           *files # legacy ctags cannot read list of files from stdin
    ]
    try:
        logging.info("Running legacy ctags")
        stdout, _ = popen(cmd, cwd=root)
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Legacy ctags failed")
        strings = []
    return [tag for string in strings for tag in legacy_tag(root, string)]

def legacy_tag(root, string):
    """Extract tag from legacy ctag output."""

    try:
        # legacy ctag -x output is 'symbol line path source_code_fragment'
        symbol, line, path = string.split()[:3]
        return [{'symbol': symbol, 'file': root/path, 'line': int(line), 'kind': None}]
    except ValueError: # not enough values to unpack, invalid literal for int()
        logging.debug('Bad legacy ctag: "%s"', string)
        return []

################################################################
