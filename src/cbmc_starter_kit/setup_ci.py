#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Set up the AWS infrastructure to run proofs in CI."""

import hashlib
import json
import logging
import shutil
import sys

import botocore.exceptions
import git

try:
    import boto3
except ModuleNotFoundError:
    logging.error("Install boto3 and try again.")
    sys.exit(1)

from cbmc_starter_kit import arguments, repository, util

################################################################


def parse_arguments():
    desc = "Set up AWS infrastructure for hosting CBMC Proof Reports."
    options = []
    args = arguments.create_parser(options, desc).parse_args()
    arguments.configure_logging(args)
    return args


################################################################


def _parse_template(cf_client, template):
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


def deploy_stack(cf_client, params):
    """Update or create stack"""
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
        logging.info("Waiting for stack to be ready...")
        waiter.wait(StackName=stack_name)
    except botocore.exceptions.ClientError as ex:
        error_message = ex.response["Error"]["Message"]
        if error_message != "No updates are to be performed.":
            logging.error(
                "When updating stack encountered unexpected error: %s",
                stack_name,
            )
            raise
        print(f"No updates are to be performed for stack {stack_name}")
    else:
        logging.info(json.dumps(stack_result, indent=4))


def deploy_ci_infrastructure(
    cf_client, github_repo_owner, github_repo_name, base_cfn_stack_folder
):
    project_specific_hash = hashlib.md5(
        f"{github_repo_owner}-{github_repo_name}".encode("utf-8")
    ).hexdigest()[:15]
    if not _stack_exists(cf_client, "proof-ci-Oidc"):
        deploy_stack(
            cf_client,
            params={
                "StackName": "proof-ci-Oidc",
                "TemplateBody": _parse_template(
                    cf_client,
                    base_cfn_stack_folder / "proof-ci-Oidc.yaml",
                ),
            },
        )
    pipeline_stack = f"proof-ci-Pipeline-{project_specific_hash}"
    ci_artifacts_bucket_name = f"proof-ci-artifacts-{project_specific_hash}"
    deploy_stack(
        cf_client,
        params={
            "StackName": pipeline_stack,
            "TemplateBody": _parse_template(
                cf_client,
                base_cfn_stack_folder / "proof-ci-Pipeline.yaml",
            ),
            "Parameters": [
                {"ParameterKey": k, "ParameterValue": v}
                for k, v in {
                    "CiArtifactsBucketName": ci_artifacts_bucket_name,
                    "GitHubRepoOwner": github_repo_owner,
                    "GitHubRepoName": github_repo_name,
                    "ProofActionsRoleName": f"proof-ci-actions-role-{project_specific_hash}",
                }.items()
            ],
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [
                {"Key": "owner", "Value": github_repo_owner},
                {"Key": "repo", "Value": github_repo_name},
            ],
        },
    )
    gh_repo_secrets_url = f"https://github.com/{github_repo_owner}/{github_repo_name}/settings/secrets/actions"
    print(
        "Please add the following secrets to your project's repository secrets at: %s",
        gh_repo_secrets_url,
    )
    response = cf_client.describe_stacks(StackName=pipeline_stack)
    outputs = response["Stacks"][0]["Outputs"]
    for output in outputs:
        key_name = output["OutputKey"]
        if key_name == "ProofActionsRoleArn":
            output_value = output["OutputValue"]
            print("PROOF_CI_IAM_ROLE = %s", output_value)
    print("PROOF_CI_AWS_REGION = %s", cf_client.meta.region_name)
    print("PROOF_CI_S3_BUCKET = %s", ci_artifacts_bucket_name)


################################################################


def main():
    """Set up the AWS infrastructure to run proofs in CI."""

    parse_arguments()  # only arguments are --verbose and --debug

    repository_root = repository.repository_root()
    github_actions_workflows_path = repository.github_actions_workflows_root()
    shutil.copytree(
        util.package_ci_workflow_template_root(),
        github_actions_workflows_path,
        dirs_exist_ok=True,
    )
    aws_account = util.ask_for_aws_account()
    repo_id = (
        git.Repo(repository_root).remotes.origin.url.split(".git")[0].split("/")
    )
    github_repo_owner, github_repo_name = repo_id[-2], repo_id[-1]
    base_cfn_stack_folder = (
        github_actions_workflows_path / util.PROOF_CI_AWS_CFN_STACKS
    )
    try:
        sts_client = boto3.client("sts")
        cf_client = boto3.client("cloudformation")
        response = sts_client.get_caller_identity()
        aws_account_in_env = response["Account"]
        if aws_account == aws_account_in_env:
            logging.info(
                "AWS credentials for account %s found", aws_account_in_env
            )
            print("Deploying CI infrastructure...")
            deploy_ci_infrastructure(
                cf_client,
                github_repo_owner,
                github_repo_name,
                base_cfn_stack_folder,
            )
        else:
            logging.error(
                "AWS credentials for %s not found", aws_account_in_env
            )
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.NoCredentialsError,
    ) as error:
        error_message = error.response["Error"]["Message"]
        logging.exception(
            f"Failed to deploy CI infrastructure: {error_message}"
        )


if __name__ == "__main__":
    main()
