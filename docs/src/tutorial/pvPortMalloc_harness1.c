// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/*
 * Insert copyright notice
 */

/**
 * @file pvPortMalloc_harness.c
 * @brief Implements the proof harness for pvPortMalloc function.
 */

/*
 * Insert project header files that
 *   - include the declaration of the function
 *   - include the types needed to declare function arguments
 */

#include <stdlib.h>
#include "FreeRTOS.h"

void * pvPortMalloc( size_t xWantedSize );

void harness()
{
  /* allocate heap */
  uint8_t app_heap[ configTOTAL_HEAP_SIZE ];

  /* initialize heap */
  HeapRegion_t xHeapRegions[] =
    {
      { ( unsigned char * ) app_heap, sizeof( app_heap ) },
      { NULL,                         0                  }
    };
  vPortDefineHeapRegions( xHeapRegions );

  /* mess up heap */
  size_t xWantedSize1, xWantedSize2, xWantedSize3;
  void* pv1 = pvPortMalloc( xWantedSize1 );
  void* pv2 = pvPortMalloc( xWantedSize2 );
  void* pv3 = pvPortMalloc( xWantedSize3 );
  vPortFree( pv2 );

  size_t xWantedSize;
  pvPortMalloc( xWantedSize );
}
