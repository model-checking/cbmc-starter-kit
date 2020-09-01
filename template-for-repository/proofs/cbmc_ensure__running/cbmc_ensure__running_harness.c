/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

/**
 * A basic negative assertion should fail
 * if CBMC was run at all.
 */
void cbmc_ensure__running_harness() {
    int lhs, rhs;
    assert(lhs == rhs);
}
