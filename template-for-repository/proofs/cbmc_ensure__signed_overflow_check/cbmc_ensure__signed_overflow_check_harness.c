/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

/**
 * A negative test for --signed-overflow-check flag
 */
void cbmc_ensure__signed_overflow_check_harness() {
    int overflow, offset;
    overflow += offset;
    overflow -= offset;
}
