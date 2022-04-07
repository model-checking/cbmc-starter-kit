/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

#include <stdint.h>

/**
 * A negative test for --conversion-check flag
 */
void conversion_check_harness() {
    uint64_t src;
    uint32_t dst = src;
}
