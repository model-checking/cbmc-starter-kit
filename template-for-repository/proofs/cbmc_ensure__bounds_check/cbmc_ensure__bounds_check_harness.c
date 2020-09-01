/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

#include <stddef.h>

/**
 * A negative test for --bounds-check flag
 */
void cbmc_ensure__bounds_check_harness() {
    char test[10];
    size_t index;
    char ch;
    test[index] = ch;
}
