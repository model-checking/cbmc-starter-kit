/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

#include <stddef.h>

/**
 * A negative test for --pointer-overflow-check flag
 */
void pointer_overflow_check_harness() {
    size_t offset;
    char *pointer;
    pointer += offset;
}
