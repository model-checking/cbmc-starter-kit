/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

/**
 * A negative test for --unsigned-overflow-check flag
 */
void cbmc_ensure__unsigned_overflow_check_harness() {
    unsigned overflow, offset;
    overflow += offset;
}
