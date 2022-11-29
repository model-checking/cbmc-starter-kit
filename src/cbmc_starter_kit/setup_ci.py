#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the AWS infrastructure to run proofs in CI."""

import json
import logging
import re
import shutil
from argparse import RawDescriptionHelpFormatter

import boto3
import botocore.exceptions
import git

from cbmc_starter_kit import arguments, repository, util

################################################################

def parse_arguments():
    """Parse arguments for cbmc-starter-kit-setup-ci command"""
    desc = """
    Adds a worflow and other resource files, such that CBMC proofs are executed
    in GitHub Actions as part of CI. If your project is a public GitHub repo,
    you can elect to deploy infrastructure to AWS, so that you can later browse
    CI artifacts online.

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
        'flag': '--aws-account-id',
        'type': lambda x: x if x.isdigit() and len(x) == 12 else False,
        'help': """
                ID of the AWS account where AWS CloudFormation stacks will be
                deployed such that CI artifacts can be viewed online.
                This option should be used only by public GitHub repositories.
                """
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

def _get_template_body(cf_client, cfn_path, stack_name):
    template = cfn_path / f"{stack_name}.yaml"
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cf_client.validate_template(TemplateBody=template_data)
    return template_data

def _stack_exists(cf_client, stack_name):
    stacks = cf_client.list_stacks()["StackSummaries"]
    for stack in stacks:
        if stack["StackStatus"] == "DELETE_COMPLETE":
            continue
        if stack_name == stack["StackName"]:
            return True
    return False

def _deploy_stack(cf_client, params):
    """Update or create AWS CloudFormation stack"""
    stack_name = params["StackName"]
    try:
        if _stack_exists(cf_client, stack_name):
            logging.info("Updating %s", stack_name)
            stack_result = cf_client.update_stack(**params)
            waiter = cf_client.get_waiter("stack_update_complete")
        else:
            logging.info("Creating %s", stack_name)
            stack_result = cf_client.create_stack(**params)
            waiter = cf_client.get_waiter("stack_create_complete")
        logging.info("Waiting for stack operation to complete...")
        waiter.wait(StackName=stack_name)
    except botocore.exceptions.ClientError as ex:
        error_message = ex.response["Error"]["Message"]
        if error_message != "No updates are to be performed.":
            logging.error(
                "When updating stack, unexpected error encountered: %s",
                stack_name,
            )
            raise
        print(f"No updates are to be performed for stack {stack_name}")
    else:
        logging.info(json.dumps(stack_result, indent=4))

def _deploy_stacks(cf_client, cfn_path, repo_owner, repo_name, repo_id):
    """
    Deploy AWS CloudFormation stacks. Return domain of CloudFront distribution
    """
    if not _stack_exists(cf_client, util.CFN_STACK_OIDC):
        _deploy_stack(
            cf_client,
            params={
                "StackName": util.CFN_STACK_OIDC,
                "TemplateBody": _get_template_body(
                    cf_client, cfn_path, util.CFN_STACK_OIDC),
            },
        )
    pipeline_stack = f"{util.CFN_STACK_PIPELINE}-{repo_id}"
    _deploy_stack(
        cf_client,
        params={
            "StackName": pipeline_stack,
            "TemplateBody": _get_template_body(
                    cf_client, cfn_path, util.CFN_STACK_PIPELINE),
            "Parameters": [
                {"ParameterKey": k, "ParameterValue": v}
                for k, v in {
                    "GitHubRepoOwner": repo_owner,
                    "GitHubRepoName": repo_name,
                    "GitHubRepoId": str(repo_id)
                }.items()
            ],
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [
                {"Key": "owner", "Value": repo_owner},
                {"Key": "repo", "Value": repo_name}
            ],
        },
    )
    print(
        "Visit:\n\n"
        f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions\n")
    print(
        "and add a \"PROOF_CI_IAM_ROLE\" secret to your GitHub repository's "
        "secrets used in GitHub Actions.\nThe secret must have this value:\n")
    response = cf_client.describe_stacks(StackName=pipeline_stack)
    outputs = response["Stacks"][0]["Outputs"]
    aws_cloudfront_domain = "''"
    for output in outputs:
        key_name = output["OutputKey"]
        if key_name == "ProofActionsRoleArn":
            print(output["OutputValue"])
        elif key_name == "ProofCIDistributionDomainName":
            aws_cloudfront_domain = output["OutputValue"]
    return aws_cloudfront_domain

def deploy(aws_account_id, cfn_path, repo_owner, repo_name, repo_id):
    """
    Deploy to AWS the infrastructure in the form of AWS CFN stacks needed to run
    CBMC proofs as part of CI.

    Return domain of CloudFront distribution that will serve CI artifacts
    """
    aws_cloudfront_domain = "''"
    try:
        sts_client = boto3.client("sts")
        cf_client = boto3.client("cloudformation")
        response = sts_client.get_caller_identity()
        if aws_account_id == response["Account"]:
            logging.info(
                "AWS credentials for account %s found", response["Account"])
            print("Deploying CI infrastructure to AWS CloudFormation...")
            aws_cloudfront_domain = _deploy_stacks(
                cf_client, cfn_path, repo_owner, repo_name, repo_id)
        else:
            logging.error(
                "AWS credentials for %s not found", response["Account"])
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.NoCredentialsError,
    ) as error:
        error_message = error.response["Error"]["Message"]
        logging.exception(
            "Failed to deploy CI infrastructure: %s", error_message)
    return aws_cloudfront_domain

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

def patch_proof_ci_workflow(args, aws_cloudfront_domain, proof_ci_path):
    """Patch GitHub Actions workflow with appropriate values"""
    lines = _read_file_template(proof_ci_path)
    proofs_dir = repository.get_relative_path_from_repository_to_proofs_root()
    replacements = {
        "AWS_CLOUDFRONT_DOMAIN": aws_cloudfront_domain,
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
    aws_account_id = args.aws_account_id
    repo_root = repository.repository_root()
    repo_url_segments = (
        git.Repo(repo_root).remotes.origin.url.split(".git")[0].split("/"))
    repo_owner, repo_name = repo_url_segments[-2], repo_url_segments[-1]

    github_actions_workflows_path = repository.github_actions_workflows_root()
    workflow_path = github_actions_workflows_path / util.GITHUB_ACTIONS_PROOF_CI
    cfn_path = github_actions_workflows_path / util.PROOF_CI_AWS_CFN_STACKS

    shutil.copytree(
        util.package_ci_workflow_template_root(),
        github_actions_workflows_path,
        dirs_exist_ok=True)

    aws_cloudfront_domain = "''"
    if aws_account_id:
        repo_details = util.get_repository_details(repo_owner, repo_name)
        repo_id = repo_details["id"]
        aws_cloudfront_domain = deploy(
            aws_account_id, cfn_path, repo_owner, repo_name, repo_id)

    patch_proof_ci_workflow(args, aws_cloudfront_domain, workflow_path)
    add_or_update_summarize_module(repo_root, quiet=not args.debug)
    if aws_cloudfront_domain == "''":
        for filename in cfn_path.iterdir():
            filename.unlink()

if __name__ == "__main__":
    main()
