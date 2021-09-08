/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

/**
 * A negative test for --undefined-shift-check flag
 */
void cbmc_ensure__undefined_shift_check_harness() {
    int base, shift;
    base <<= shift;
    base >>= shift;
}
