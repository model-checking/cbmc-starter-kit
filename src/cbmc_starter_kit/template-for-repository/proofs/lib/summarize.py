# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import argparse
import json
import logging


DESCRIPTION = """Print 2 tables in GitHub-flavored Markdown that summarize
an execution of CBMC proofs."""
EPILOG = """The CloudFront domain and the S3 URI should either be specified
 together or they should not be specified altogether."""


def get_args():
    """Parse arguments for summarize script."""
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
    for arg in [{
            "flags": ["--run-file"],
            "help": "path to the Litani run.json file",
            "required": True,
        }, {
            "flags": ["--cloudfront-domain"],
            "help": "the domain of the Amazon CloudFront distribution that is "
                    "serving CBMC proof reports, which were uploaded to S3"
                    "during the execution of the GitHub Actions workflow."
                    "Usage of this flag necessitates usage of --s3-uri"
                    "For example: d111111abcdef8.cloudfront.net"
        }, {
            "flags": ["--s3-uri"],
            "help": "the key to a directory within a S3 bucket holding all "
                    "artifacts for a CBMC proof report."
                    "Usage of this flag necessitates usage of --cloudfront-domain"
                    "For example: BuildArtifacts/abcdef/final"
    }]:
        flags = arg.pop("flags")
        parser.add_argument(*flags, **arg)
    args = parser.parse_args()
    with_aws = args.cloudfront_domain and args.s3_uri
    without_aws = not args.cloudfront_domain and not args.s3_uri
    if not (with_aws or without_aws):
        parser.error(
            "The CloudFront domain and the S3 URI should either be specified "
            "together or they should not be specified altogether.")
    return args


def _get_max_length_per_column_list(data):
    ret = [len(item) + 1 for item in data[0]]
    for row in data[1:]:
        for idx, item in enumerate(row):
            ret[idx] = max(ret[idx], len(item) + 1)
    return ret


def _get_table_header_separator(max_length_per_column_list):
    line_sep = ""
    for max_length_of_word_in_col in max_length_per_column_list:
        line_sep += "|" + "-" * (max_length_of_word_in_col + 1)
    line_sep += "|\n"
    return line_sep


def _get_entries(max_length_per_column_list, row_data):
    entries = []
    for row in row_data:
        entry = ""
        for idx, word in enumerate(row):
            max_length_of_word_in_col = max_length_per_column_list[idx]
            space_formatted_word = (max_length_of_word_in_col - len(word)) * " "
            entry += "| " + word + space_formatted_word
        entry += "|\n"
        entries.append(entry)
    return entries


def _get_rendered_table(data):
    table = []
    max_length_per_column_list = _get_max_length_per_column_list(data)
    entries = _get_entries(max_length_per_column_list, data)
    for idx, entry in enumerate(entries):
        if idx == 1:
            line_sep = _get_table_header_separator(max_length_per_column_list)
            table.append(line_sep)
        table.append(entry)
    table.append("\n")
    return "".join(table)


def _get_status_and_proof_summaries(run_dict, cloudfront_domain=None, s3_uri=None):
    """Parse a dict representing a Litani run and create lists summarizing the
    proof results.

    Parameters
    ----------
    run_dict
        A dictionary representing a Litani run.
    cloudfront_domain
        A string representing the domain of the CloudFront distribution, which
        serves CBMC proof results that areuploaded to an associated S3 bucket.
        For example: d111111abcdef8.cloudfront.net
    s3_uri
        The key to a directory within a S3 bucket holding all artifacts for a
        CBMC proof report.
        For example: BuildArtifacts/abcdef/final

    Returns
    -------
    A list of 2 lists.
    The first sub-list maps a status to the number of proofs with that status.
    The second sub-list maps each proof to its status.
    """
    count_statuses = {}
    proofs = [["Proof", "Status"]]
    if cloudfront_domain:
        proofs[0].append("CBMC proof report")
    for proof_pipeline in run_dict["pipelines"]:
        status_pretty_name = proof_pipeline["status"].title().replace("_", " ")
        try:
            count_statuses[status_pretty_name] += 1
        except KeyError:
            count_statuses[status_pretty_name] = 1
        proof = proof_pipeline["name"]
        proofs.append([proof, status_pretty_name])
    if cloudfront_domain:
        for i in range(1, len(proofs)):
            proof = proofs[i][0]
            final_report = f"https://{cloudfront_domain}/{s3_uri}"
            viewer_proof_artifact = f"artifacts/{proof}/report/html/index.html"
            viewer_html_report_url = f"{final_report}/{viewer_proof_artifact}"
            proofs[i].append(f"[Details]({viewer_html_report_url})")
    statuses = [["Status", "Count"]]
    for status, count in count_statuses.items():
        statuses.append([status, str(count)])
    return [statuses, proofs]


def print_proof_results(out_file, cloudfront_domain=None, s3_uri=None):
    """
    Print 2 strings that summarize the proof results.
    When printing, each string will render as a GitHub flavored Markdown table.
    """
    print("## Summary of CBMC proof results")
    try:
        with open(out_file, encoding='utf-8') as run_json:
            run_dict = json.load(run_json)
            summaries = _get_status_and_proof_summaries(
                run_dict, cloudfront_domain=cloudfront_domain, s3_uri=s3_uri)
            for summary in summaries:
                print(_get_rendered_table(summary))
    except Exception as ex: # pylint: disable=broad-except
        logging.critical("Could not print results. Exception: %s", str(ex))


if __name__ == '__main__':
    args = get_args()
    without_aws = not args.cloudfront_domain and not args.s3_uri
    if without_aws:
        print_proof_results(args.run_file)
        exit(0)
    CBMC_PROOF_REPORT_HEADER = "Click here to see the CBMC proof report"
    url = f"https://{args.cloudfront_domain}/{args.s3_uri}/index.html"
    print(f"## [{CBMC_PROOF_REPORT_HEADER}]({url})")
    print_proof_results(
        args.run_file,
        cloudfront_domain=args.cloudfront_domain,
        s3_uri=args.s3_uri)
