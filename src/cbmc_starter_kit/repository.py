"""Discover repository properties like repository root, proof root, etc."""

from pathlib import Path
from subprocess import Popen, PIPE
import json
import logging

import git

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

    try:
        root = git.Repo(cwd, search_parent_directories=True).working_dir
        return Path(root) if abspath else path_to_ancestor(cwd, root)
    except git.InvalidGitRepositoryError:
        raise UserWarning(f"No git repository contains {cwd}") from None

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

def submodule_root(url, submodules=None, repo='.', abspath=True):
    """Look up path to root of submodule url in submodules."""

    url = url.lower()
    repo = repository_root(repo)
    submodules = submodules or git.Repo(repo).submodules

    for submodule in submodules:
        if not submodule.url.lower() in [url, url+".git"]:
            continue
        return repo/submodule.path if abspath else Path(submodule.path)

    logging.debug("Can't find submodule '%s'", url)
    logging.debug("Found submodules = %s", submodules)
    return None


def litani_root(submodules=None, repo='.', abspath=True):
    """Root of litani submodule."""

    repo = repository_root(repo)
    submodules = submodules or git.Repo(repo).submodules
    litani1 = 'https://github.com/awslabs/aws-build-accumulator'
    litani2 = 'git@github.com:awslabs/aws-build-accumulator'
    return (submodule_root(litani1, submodules, repo, abspath) or
            submodule_root(litani2, submodules, repo, abspath))

def starter_kit_root(submodules=None, repo='.', abspath=True):
    """Root of starter kit submodule."""

    repo = repository_root(repo)
    submodules = submodules or git.Repo(repo).submodules
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
