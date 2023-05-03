# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Version number."""

import os

NAME = "CBMC starter kit"
NUMBER = "2.10"
VERSION = f"{NAME} {NUMBER}"

REPLACE_TARGET = '_CBMC_STARTER_KIT_VERSION_'

def version(display=False):
    """The version of cbmc viewer."""

    if display:
        print(VERSION)
    return VERSION

def copy_with_version(src, dst):
    with open(src, encoding='utf-8') as srcfile:
        data = srcfile.read()
    with open(dst, 'w', encoding='utf-8') as dstfile:
        dstfile.write(data.replace(REPLACE_TARGET, version()))

def update_existing_version_in_workflow_file(workflow):
    tmp_file = f"{workflow}~"
    with open(workflow) as src, open(tmp_file, "w") as dst:
        for line in src:
            if line.startswith(f"# {NAME}"):
                print(version(), file=dst)
            else:
                print(line, file=dst)
    os.rename(tmp_file, workflow)
