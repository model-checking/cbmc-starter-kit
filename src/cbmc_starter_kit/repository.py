"""Discover repository properties like repository root, proof root, etc."""

from pathlib import Path
from subprocess import Popen, PIPE
import subprocess
import logging
import json
import re

################################################################
# Construct an ascending relative path like "../../.." from a
# directory to an ancestor in the file system.
#
# The Path method dst.relative_to(src) requires that dst is a
# descendant of src and will not produce a path like "../../..".

def path_to_ancestor(descendant, ancestor):
    """Relative path from descendant to ancestor."""

    descendant = Path(descendant).resolve()
    ancestor = Path(ancestor).resolve()

    try:
        path = descendant.relative_to(ancestor)
    except ValueError:
        raise UserWarning(f"{ancestor} is not an ancestor of {descendant}") from ValueError

    return Path(*[Path('..') for part in path.parts])

################################################################
# Discover the roots of
#   * the respository and
#   * the proofs subtree installed by the starter kit.

def repository_root(cwd='.', abspath=True):
    """Path to root of repository containing current directory.

    Return the absolute path if abspath is True.  If abspath is False,
    return the relative path from the current directory.  If the
    current directory is within a submodule of the repository, then
    the root of the submodule is returned, not the repository itself.
    """

    cwd = Path(cwd).resolve()
    for ancestor in [cwd, *cwd.parents]:
        if (ancestor / '.git').is_dir():
            return ancestor if abspath else path_to_ancestor(cwd, ancestor)
    raise UserWarning(f"No git repository contains {cwd}")

def proofs_root(cwd='.', abspath=True):
    """Path to root of proofs subtree installed by starter kit.

    Return an absolute path if abspath is True, and a path relative to
    cwd otherwise.  Search starts at cwd and ascends until it reaches
    the root of the enclosing repository, and raises UserWarning if
    there is no enclosing repository."""

    cwd = Path(cwd).resolve()                     # Where to start looking
    root = repository_root(cwd=cwd, abspath=True) # Where to stop looking
    proofs = "proofs"                             # What to look for

    for path in [cwd, *cwd.parents]:
        if path.name == proofs:
            return path if abspath else path_to_ancestor(cwd, path)
        if path == root:
            break
    raise UserWarning(f"'{cwd}' has no ancestor named '{proofs}'")

################################################################
# Discover the roots of
#   * the litani submodule
#   * the starter kit submodule

def load_submodules(repo=None):
    """Load file .gitmodules describing the installed submodules"""

    repo = repo or repository_root()
    try:
        cmd = ['git', 'config', '-f', '.gitmodules', '--list']
        kwds = {'cwd': str(repo), 'capture_output': True, 'text': True}
        lines = subprocess.run(cmd, **kwds, check=True).stdout.splitlines()
    except subprocess.CalledProcessError as error:
        logging.debug(error)
        raise UserWarning(
            f"Can't load submodules in repository root '{repo}'"
        ) from error

    submodules = {}
    for line in lines:
        line=re.sub(r'\s+', ' ', line.strip())

        # Output of git config is lines of the form
        #   submodule.ORGANIZATION/REPOSITORY.path=PATH
        #   submodule.ORGANIZATION/REPOSITORY.url=URL
        # Parsing config output with a simple regular expression will
        # fail if PATH or URL contains path= or url= as a substring.
        match = re.match(r"^submodule\.(.+)\.(path|url)=(.+)", line)
        if not match:
            logging.debug("Can't parse git config output: '%s'", line)
            continue

        name, key, value = [string.strip() for string in match.groups()[0:3]]
        if key == 'path':
            value = Path(value)
            if not value.is_dir(): # Maybe PATH included path= as a substring...
                logging.debug("Not a directory: path %s for submodule %s", value, name)
        submodules[name] = submodules.get(name, {})
        submodules[name][key] = value

    return submodules

def submodule_root(url, submodules=None, repo=None, abspath=True):
    """Look up path to root of submodule url in submodules."""

    url = url.lower()
    repo = Path(repo) if repo else repository_root()
    submodules = submodules or load_submodules(repo=repo)

    for _, config in submodules.items():
        config_url = config.get("url")
        config_path = config.get("path")

        if not config_url or not config_url.lower() in [url, url+".git"]:
            continue
        if not config_path:
            logging.debug("Can't find path to submodule '%s'", url)
            logging.debug("Found submodule config = %s", config)
            return None
        return repo/config_path if abspath else config_path

    logging.debug("Can't find submodule '%s'", url)
    logging.debug("Found submodules = %s", submodules)
    return None


def litani_root(submodules=None, repo=None, abspath=True):
    """Root of litani submodule."""

    litani1 = 'https://github.com/awslabs/aws-build-accumulator'
    litani2 = 'git@github.com:awslabs/aws-build-accumulator'
    return (submodule_root(litani1, submodules, repo, abspath) or
            submodule_root(litani2, submodules, repo, abspath))

def starter_kit_root(submodules=None, repo=None, abspath=True):
    """Root of starter kit submodule."""

    old_starter1 = 'https://github.com/awslabs/aws-templates-for-cbmc-proofs'
    old_starter2 = 'git@github.com:awslabs/aws-templates-for-cbmc-proofs'
    new_starter1 = 'https://github.com/model-checking/cbmc-starter-kit'
    new_starter2 = 'git@github.com:model-checking/cbmc-starter-kit'
    return (submodule_root(old_starter1, submodules, repo, abspath) or
            submodule_root(old_starter2, submodules, repo, abspath) or
            submodule_root(new_starter1, submodules, repo, abspath) or
            submodule_root(new_starter2, submodules, repo, abspath))

################################################################
# Discover the set of all source files in the repository that define a
# function named func.

def run(cmd, cwd=None, stdin=None):
    """Run a command with string stdin on stdin, return stdout and stderr."""

    cmd = [str(word) for word in cmd]
    try:
        with Popen(cmd, cwd=cwd, text=True, stdin=PIPE, stdout=PIPE, stderr=PIPE) as pipe:
            stdout, stderr = pipe.communicate(input=stdin)
        if pipe.returncode:
            logging.debug("Nonzero return code %s: command: '%s'", pipe.returncode, ' '.join(cmd))
            logging.debug("Nonzero return code %s: stderr: '%s'", pipe.returncode, pipe.stderr)
            return None, None
        return stdout, stderr
    except FileNotFoundError:
        logging.debug("FileNotFoundError: command '%s'", ' '.join(cmd))
        return None, None

def function_tags(repo='.'):
    """List of tags for function definitions in respository source files.

    Each tag is a dict '{"name": function, "path": source}' naming a
    function and a source file defining the function."""

    repo = Path(repo).resolve()

    find_cmd = ['find', '.', '-name', '*.c']
    find_stdout, _ = run(find_cmd, cwd=repo)
    if find_stdout is None: # run() logs errors on debug
        return []

    ctags_cmd = [
        'ctags',
        '-L', '-', # read from standard input
        '--c-types=f', # include only function definition tags
        '--output-format=json', # each line is one json blob for one tag
        '--fields=NF' # each json blob is {name="function", path="source"}
    ]
    ctags_stdout, _ = run(ctags_cmd, cwd=repo, stdin=find_stdout)
    if ctags_stdout is None: # run() logs errors on debug
        return []

    blobs = ctags_stdout.splitlines()  # a list of json blobs
    blob = '[' + ','.join(blobs) + ']' # a json blob
    try:
        return json.loads(blob)
    except json.decoder.JSONDecodeError as error:
        logging.debug("Can't load json output of ctags in %s", repo)
        logging.debug(error)
        return []

def function_paths(func, tags):
    """Paths to all source files in tags defining a function func."""

    return sorted([tag['path'] for tag in tags if tag['name'] == func])

def function_sources(func, cwd='.', repo='.', abspath=True):
    """Paths to all source files in the repository defining a function func.

    Paths are absolute if abspath is True, and relative to cwd otherwise.

    """

    cwd = Path(cwd).resolve()
    repo = Path(repo).resolve()

    tags = function_tags(repo)
    paths = function_paths(func, tags)

    path_to_repo = repo if abspath else path_to_ancestor(cwd, repo)
    sources = [Path(path_to_repo, path) for path in paths]

    assert all(src.is_file() for src in sources)
    return sources

################################################################
