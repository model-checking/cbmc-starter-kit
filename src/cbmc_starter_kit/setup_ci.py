#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the AWS infrastructure to run proofs in CI."""

import logging
import shutil
from argparse import RawDescriptionHelpFormatter


from cbmc_starter_kit import arguments, repository, util, version

################################################################

def parse_arguments():
    """Parse arguments for cbmc-starter-kit-setup-ci command"""
    desc = """
    Copy a GitHub Action workflow to `.github/workflows` in this repository,
    which runs CBMC proofs on every push event.
    """
    eplg = """
    The most recently released and available version of a tool (like CBMC, CBMC
    viewer, Litani, kissat, cadical) will be used by default. If the latest
    version of a tool does not work with some proofs, use one of the flags above
    to specify a particular version of the tool to pin to.
    
    Previous releases for each tool are listed here:
    - https://github.com/diffblue/cbmc/releases
    - https://github.com/model-checking/cbmc-viewer/releases
    - https://github.com/awslabs/aws-build-accumulator/releases
    - https://github.com/arminbiere/kissat/tags
    - https://github.com/arminbiere/cadical/tags
    """
    options = [{
        'flag': '--github-actions-runner',
        'metavar': '<name-of-GitHub-hosted-runner-operating-on-Ubuntu-20.04>',
        'default': 'ubuntu-20.04',
        'help': """
                The GitHub-hosted runner (operating on Ubuntu 20.04) that will
                run CBMC proofs in GitHub Actions. If your repo has a large
                runner available, you can specify it here. default: %(default)s"""
        }, {
        'flag': '--cbmc',
        'metavar': '<X.Y.Z>',
        'default': 'latest',
        'help': 'Use this version of CBMC in CI. default: %(default)s'
        }, {
        'flag': '--cbmc-viewer',
        'metavar': '<X.Y>',
        'default': 'latest',
        'help': 'Use this version of CBMC viewer in CI. default: %(default)s'
        }, {
        'flag': '--litani',
        'metavar': '<X.Y.Z>',
        'default': 'latest',
        'help': 'Use this version of Litani in CI. default: %(default)s'
        }, {
        'flag': '--kissat',
        "metavar": '<TAG>',
        'default': 'latest',
        'help': 'Use this tag of kissat in CI. default: %(default)s'
        }, {
        'flag': '--cadical',
        "metavar": '<TAG>',
        'default': 'latest',
        'help': 'Use this tag of cadical in CI. default: %(default)s'
        }]
    args = arguments.create_parser(
        options=options,
        description=desc,
        epilog=eplg,
        formatter_class=RawDescriptionHelpFormatter).parse_args()
    arguments.configure_logging(args)
    return args

################################################################

def _replace_placeholders_in_config_template(lines, replacements):
    """Returns a list of new lines, where some lines have had a placeholder
    value appropriately updated."""
    buf = []
    for line in lines:
        if not line or line[-1] != ">":
            buf.append(line)
            continue
        key_lower_kebab = line.split(":")[0]
        key_upper_snake = key_lower_kebab.replace('-', '_').upper()
        buf.append(f"{key_lower_kebab}: {replacements[key_upper_snake]}")
    return buf

def patch_proof_ci_config(config, args):
    """Patch config for GitHub Actions workflow with appropriate values"""
    with open(config, encoding='utf-8') as data:
        lines = data.read().splitlines()
    proofs_dir = repository.get_relative_path_from_repository_to_proofs_root()
    replacements = {
        "CADICAL_TAG": args.cadical,
        "CBMC_VERSION": args.cbmc,
        "CBMC_VIEWER_VERSION": args.cbmc_viewer,
        "KISSAT_TAG": args.kissat,
        "LITANI_VERSION": args.litani,
        "PROOFS_DIR": proofs_dir,
    }
    new_lines = _replace_placeholders_in_config_template(lines, replacements)
    with open(config, "w", encoding='utf-8') as data:
        data.write('\n'.join(new_lines) + '\n')

def patch_proof_ci_workflow(workflow, github_actions_runner):
    """Patch GitHub Actions workflow with appropriate GitHub-hosted runner"""
    with open(workflow, encoding='utf-8') as data:
        lines = data.read().splitlines()
    new_lines = []
    for line in lines:
        if line.strip() == "runs-on: <__GITHUB_ACTIONS_RUNNER__>":
            new_line = line.replace(
                "<__GITHUB_ACTIONS_RUNNER__>", github_actions_runner)
            new_lines.append(new_line)
            continue
        new_lines.append(line)
    with open(workflow, "w", encoding='utf-8') as data:
        data.write('\n'.join(new_lines) + '\n')

################################################################

def copy_lib_directory(repo_root):
    """Will either add or update the "summarize" module located within the CBMC
    proof root's lib module"""
    logging.debug('Updating CBMC starter kit')
    src = util.package_repository_template_root() / util.PROOF_DIR / util.LIB_MODULE
    dst = repository.get_abspath_to_proofs_root(repo_root) / util.LIB_MODULE
    logging.info('Copying template lib module from %s to %s', src, dst)
    assert src.exists()
    shutil.copytree(src, dst, dirs_exist_ok=True)

################################################################

def main():
    """
    Creates a GitHub Actions workflow file based on the provided input.
    """
    args = parse_arguments()

    workflows_root = repository.github_actions_workflows_root()
    config = workflows_root / "proof_ci_resources" / "config.yaml"
    workflow = workflows_root / "proof_ci.yaml"

    shutil.copytree(
        util.package_ci_workflow_template_root(),
        workflows_root,
        dirs_exist_ok=True)

    patch_proof_ci_config(config, args)
    patch_proof_ci_workflow(workflow, args.github_actions_runner)
    version.copy_with_version(workflow, workflow)

    repo_root = repository.repository_root()
    copy_lib_directory(repo_root)

if __name__ == "__main__":
    main()
