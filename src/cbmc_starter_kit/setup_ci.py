#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the AWS infrastructure to run proofs in CI."""

import json
import logging
import shutil
from argparse import ArgumentTypeError, RawDescriptionHelpFormatter

import boto3
import botocore.exceptions
import git

from cbmc_starter_kit import arguments, repository, util

################################################################

def is_valid_aws_account_id(aws_account_id):
    if not aws_account_id or not (aws_account_id.isdigit() and len(aws_account_id) == 12):
        raise ArgumentTypeError(
            "AWS account ID is a 12-character string consisting only of digits")
    return aws_account_id

def parse_arguments():
    """Parse arguments for cbmc-starter-kit-setup-ci command"""
    desc = """
    Copy a GitHub Action workflow to `.github/workflows` in this repository,
    which runs CBMC proofs on every push event.
    If your project is a public GitHub repo, you can elect to provision
    infrastructure in AWS, such that you can browse CI artifacts online.
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
        'flag': '--aws-account-id',
        'type': is_valid_aws_account_id,
        'help': """
                ID of the AWS account, where AWS CloudFormation stacks will be
                deployed so that CI artifacts can be viewed online.
                This option should be used only by public GitHub repositories.
                """
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
                "When updating stack %s, unexpected error encountered: %s",
                stack_name, error_message
            )
            raise
        print(f"No updates are to be performed for stack {stack_name}")
    else:
        logging.info("Deployment result for stack '%s':", stack_name)
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

def deploy(aws_account_id, cfn_path, repo_owner, repo_name, repo_id):
    """
    Deploy to AWS the infrastructure in the form of AWS CFN stacks needed to run
    CBMC proofs as part of CI.
    """
    try:
        sts_client = boto3.client("sts")
        cf_client = boto3.client("cloudformation")
        response = sts_client.get_caller_identity()
        if aws_account_id == response["Account"]:
            logging.info(
                "AWS credentials for account %s found", response["Account"])
            print("Deploying CI infrastructure to AWS CloudFormation...")
            _deploy_stacks(
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

def get_pipeline_stack_outputs(repo_id):
    pipeline_stack = f"{util.CFN_STACK_PIPELINE}-{repo_id}"
    cf_client = boto3.client("cloudformation")
    response = cf_client.describe_stacks(StackName=pipeline_stack)
    return response["Stacks"][0]["Outputs"]

def print_role_arn(pipeline_outputs, repo_owner, repo_name):
    for output in pipeline_outputs:
        if output["OutputKey"] == "ProofActionsRoleArn":
            role_arn = output["OutputValue"]
            print(
                "Visit:\n\n"
                f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions\n\n"
                "and add a \"PROOF_CI_IAM_ROLE\" secret to your repository's "
                f"secrets used in GitHub Actions.\nThe secret must have this value:\n\n{role_arn}")
            return

def get_aws_cloudfront_domain(pipeline_outputs):
    for output in pipeline_outputs:
        if output["OutputKey"] == "ProofCIDistributionDomainName":
            return output["OutputValue"]

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

def patch_proof_ci_config(config, args, domain_name):
    """Patch config for GitHub Actions workflow with appropriate values"""
    with open(config, encoding='utf-8') as data:
        lines = data.read().splitlines()
    proofs_dir = repository.get_relative_path_from_repository_to_proofs_root()
    replacements = {
        "AWS_CLOUDFRONT_DOMAIN": domain_name,
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
    aws_account_id = args.aws_account_id
    repo_root = repository.repository_root()
    repo_url_segments = (
        git.Repo(repo_root).remotes.origin.url.split(".git")[0].split("/"))
    repo_owner, repo_name = repo_url_segments[-2], repo_url_segments[-1]

    workflows_root = repository.github_actions_workflows_root()
    config = workflows_root / "proof_ci_resources" / "config.yaml"
    workflow = workflows_root / "proof_ci.yaml"

    shutil.copytree(
        util.package_ci_workflow_template_root(),
        workflows_root,
        dirs_exist_ok=True)

    # If the workflow is provided with an empty string as the CloudFront domain,
    # then steps relevant to AWS will not be executed in GitHub Actions
    domain_name = "''"
    if aws_account_id:
        cfn_path = workflows_root / "proof_ci_resources" / "cfn"
        repo_id = util.get_repo_id(repo_owner, repo_name)
        deploy(aws_account_id, cfn_path, repo_owner, repo_name, repo_id)
        pipeline_stack_outputs = get_pipeline_stack_outputs(repo_id)
        print_role_arn(pipeline_stack_outputs, repo_owner, repo_name)
        domain_name = get_aws_cloudfront_domain(pipeline_stack_outputs)
        if not domain_name or domain_name == "''":
            # Delete templates from target repository
            for filename in cfn_path.iterdir():
                filename.unlink()

    patch_proof_ci_config(config, args, domain_name)
    patch_proof_ci_workflow(workflow, args.github_actions_runner)

    repo_root = repository.repository_root()
    copy_lib_directory(repo_root)

if __name__ == "__main__":
    main()
