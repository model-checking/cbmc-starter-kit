/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

/**
 * A negative test for --nan-check flag
 */
void nan_check_harness() {
    float nan;
    nan = nan / nan;
}
