/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

#include <stdint.h>

/**
 * A negative test for --conversion-check flag
 */
void cbmc_ensure__conversion_check_harness() {
    uint64_t src;
    uint32_t dst = src;
}
