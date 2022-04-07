/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT-0.
 */

/**
 * A negative test for --pointer-primitive-check flag
 */
void pointer_primitive_check_harness() {
    char *pointer;
    assert(__CPROVER_r_ok(pointer, 10));
}
