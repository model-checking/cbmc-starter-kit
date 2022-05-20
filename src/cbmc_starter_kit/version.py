# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Version number."""

NAME = "CBMC starter kit"
NUMBER = "2.3"
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
