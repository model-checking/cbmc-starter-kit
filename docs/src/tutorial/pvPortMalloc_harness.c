/**
 * @file pvPortMalloc_harness.c
 * @brief Implements the proof harness for pvPortMalloc function.
 */

#include <stdlib.h>
#include "FreeRTOS.h"
void *pvPortMalloc(size_t size);

void harness()
{
  size_t size;
  pvPortMalloc(size);
}
