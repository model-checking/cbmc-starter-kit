/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

#include <stddef.h>

/**
 * A negative test for --bounds-check flag
 */
void bounds_check_harness() {
    char test[10];
    size_t index;
    char ch;
    test[index] = ch;
}
