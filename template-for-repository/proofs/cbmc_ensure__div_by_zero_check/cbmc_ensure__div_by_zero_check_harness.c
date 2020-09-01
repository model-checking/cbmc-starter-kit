/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

/**
 * A negative test for --div-by-zero-check flag
 */
void cbmc_ensure__div_by_zero_check_harness() {
    int num, den;
    int div = num / den;
}
