/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

/**
 * A basic negative assertion should fail
 * if CBMC was run at all.
 */
void assert_harness() {
    int lhs, rhs;
    assert(lhs == rhs);
}
