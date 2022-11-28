#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the AWS infrastructure to run proofs in CI."""

import logging
import re
import shutil
from argparse import RawDescriptionHelpFormatter


from cbmc_starter_kit import arguments, repository, util

################################################################

def parse_arguments():
    """Parse arguments for cbmc-starter-kit-setup-ci command"""
    desc = """
    Adds a worflow and other resource files, such that CBMC proofs are executed
    in GitHub Actions as part of CI.

    The most recently released and available versions of CBMC, CBMC viewer,
    Litani, kissat and cadical will be used by default. In the cases of CBMC,
    CBMC viewer and Litani, semantic versions can be specified (e.g. '5.71.0'
    for CBMC, '3.6' for CBMC viewer, '1.27.0' for Litani). In the cases of
    kissat and cadical, any released tag can be specified (e.g. 'rel-3.0.0' and
    'rel-1.5.3' respectively).

    To find semantic versions for these tools or tags for the solvers, visit:
    - https://github.com/diffblue/cbmc/releases
    - https://github.com/model-checking/cbmc-viewer/releases
    - https://github.com/awslabs/aws-build-accumulator/releases
    - https://github.com/arminbiere/kissat/tags
    - https://github.com/arminbiere/cadical/tags
    """
    options = [{
        'flag': '--github-actions-runner',
        'required': True,
        'metavar': "<ubuntu-20.04>|<name-of-your-Ubuntu-20.04-large-runner>",
        'help': """
                The name of the Ubuntu 20.04 GitHub-hosted runner that will run
                proofs inside of GitHub Actions. For example: 'ubuntu-20.04'
                If you have created a large runner for your repo, you can
                specify its name."""
        }, {
        'flag': '--cbmc',
        'metavar': '<latest>|<X.Y.Z>',
        'default': 'latest',
        'help': "Use this version of CBMC in CI. default: %(default)s"
        }, {
        'flag': '--cbmc-viewer',
        'metavar': '<latest>|<X.Y>',
        'default': 'latest',
        'help': "Use this version of CBMC viewer in CI. default: %(default)s"
        }, {
        'flag': '--litani',
        'metavar': '<latest>|<X.Y.Z>',
        'default': 'latest',
        'help': "Use this version of Litani in CI. default: %(default)s"
        }, {
        'flag': '--kissat',
        "metavar": "<latest>|<TAG>",
        'default': 'latest',
        'help': "Use this tag of kissat in CI. default: %(default)s"
        }, {
        'flag': '--cadical',
        "metavar": "<latest>|<TAG>",
        'default': 'latest',
        'help': "Use this tag of cadical in CI. default: %(default)s"
        }]
    args = arguments.create_parser(
        options=options,
        description=desc,
        formatter_class=RawDescriptionHelpFormatter).parse_args()
    arguments.configure_logging(args)
    return args

################################################################

def _read_file_template(path):
    """Read file and return list of lines"""
    with open(path, encoding='utf-8') as data:
        return data.read().splitlines()

def _write_file_template(lines, path):
    """Write file at specified path with the provided list of lines"""
    with open(path, "w", encoding='utf-8') as data:
        data.write('\n'.join(lines) + '\n')

def _replace_placeholders_in_workflow_template(lines, replacements):
    """Returns a list of new lines, where some lines have had a placeholder
    value appropriately updated."""
    buf = []
    cmpl = re.compile(r"\s+(?P<key>[\w_]+):\s<__[\w_]+__>")
    for line in lines:
        if not line or line[len(line) - 1] != ">":
            # Append immediately if empty line or line does not end with '>'
            buf.append(line)
            continue
        if line.strip() == "runs-on: <__GITHUB_ACTIONS_RUNNER__>":
            key = "GITHUB_ACTIONS_RUNNER"
            buf.append(line.replace(f"<__{key}__>", replacements[key]))
            continue
        match = cmpl.match(line)
        if match is None:
            buf.append(line)
        else:
            key = match['key']
            buf.append(line.replace(f"<__{key}__>", replacements[key]))
    return buf

def patch_proof_ci_workflow(args, proof_ci_path):
    """Patch GitHub Actions workflow with appropriate values"""
    lines = _read_file_template(proof_ci_path)
    proofs_dir = repository.get_relative_path_from_repository_to_proofs_root()
    replacements = {
        "CADICAL_TAG": args.cadical,
        "CBMC_VERSION": args.cbmc,
        "CBMC_VIEWER_VERSION": args.cbmc_viewer,
        "GITHUB_ACTIONS_RUNNER": args.github_actions_runner,
        "KISSAT_TAG": args.kissat,
        "LITANI_VERSION": args.litani,
        "PROOFS_DIR": proofs_dir,
    }
    new_lines = _replace_placeholders_in_workflow_template(lines, replacements)
    _write_file_template(new_lines, proof_ci_path)

################################################################

def add_or_update_summarize_module(repo_root, quiet=False):
    """Will either add or update the "summarize" module located within the CBMC
    proof root's lib module"""
    logging.debug('Updating CBMC starter kit')
    src = util.package_repository_template_root() / util.PROOF_DIR / util.LIB_MODULE
    dst = repository.get_abspath_to_proofs_root(repo_root) / util.LIB_MODULE
    (logging.debug if quiet else logging.info)('Updating summarize script: %s -> %s', src, dst)
    assert src.exists()
    shutil.copytree(src, dst, dirs_exist_ok=True)

################################################################

def main():
    """
    Creates a GitHub Actions workflow file based on the provided input.
    """
    args = parse_arguments()
    repo_root = repository.repository_root()

    github_actions_workflows_path = repository.github_actions_workflows_root()
    workflow_path = github_actions_workflows_path / util.GITHUB_ACTIONS_PROOF_CI

    shutil.copytree(
        util.package_ci_workflow_template_root(),
        github_actions_workflows_path,
        dirs_exist_ok=True)

    patch_proof_ci_workflow(args, workflow_path)
    add_or_update_summarize_module(repo_root, quiet=not args.debug)

if __name__ == "__main__":
    main()
