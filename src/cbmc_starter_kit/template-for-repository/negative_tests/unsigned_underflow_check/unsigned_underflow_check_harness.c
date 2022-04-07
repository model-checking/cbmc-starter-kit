/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

/**
 * A negative test for --unsigned-overflow-check flag
 */
void unsigned_underflow_check_harness() {
    unsigned underflow, offset;
    underflow -= offset;
}
