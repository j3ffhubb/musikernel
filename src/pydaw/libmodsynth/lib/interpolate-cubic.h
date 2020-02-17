/*
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef INTERPOLATE_CUBIC_H
#define	INTERPOLATE_CUBIC_H

#include "lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

float f_cubic_interpolate_ptr_wrap(float*, int, float);
inline float f_cubic_interpolate_ptr(float*, float);

#ifdef	__cplusplus
}
#endif

/* inline float f_cubic_interpolate(
 * float a_a, //item 0
 * float a_b, //item 1
 * float a_position)  //position between the 2, range:  0 to 1
 */
/*
inline float f_cubic_interpolate(float a_a, float a_b, float a_position)
{
    return (((a_a - a_b) * a_position) + a_a);
}
*/


/* float f_cubic_interpolate_ptr_wrap(
 * float * a_table,
 * int a_table_size,
 * float a_ptr,
 * t_cubic_interpolater * a_cubic)
 *
 * This method uses a pointer instead of an array the float* must be malloc'd
 * to (sizeof(float) * a_table_size)
 */
float f_cubic_interpolate_ptr_wrap(float * a_table, int a_table_size,
        float a_ptr)
{
    int int_pos = (int)a_ptr;
    float mu = (float)a_ptr - (float)int_pos;
    float mu2 = mu * mu;
    int int_pos_plus1 = int_pos + 1;
    int int_pos_minus1 = int_pos - 1;
    int int_pos_minus2 = int_pos - 2;

    if(unlikely(int_pos >= a_table_size))
    {
        int_pos = int_pos - a_table_size;
    }
    else if(unlikely(int_pos < 0))
    {
        int_pos = int_pos + a_table_size;
    }

    if(unlikely(int_pos_plus1 >= a_table_size))
    {
        int_pos_plus1 = int_pos_plus1 - a_table_size;
    }
    else if(unlikely(int_pos_plus1 < 0))
    {
        int_pos_plus1 = int_pos_plus1 + a_table_size;
    }

    if(unlikely(int_pos_minus1 >= a_table_size))
    {
        int_pos_minus1 = int_pos_minus1 - a_table_size;
    }
    else if(unlikely(int_pos_minus1 < 0))
    {
        int_pos_minus1 = int_pos_minus1 + a_table_size;
    }

    if(unlikely(int_pos_minus2 >= a_table_size))
    {
        int_pos_minus2 = int_pos_minus2 - a_table_size;
    }
    else if(unlikely(int_pos_minus2 < 0))
    {
        int_pos_minus2 = int_pos_minus2 + a_table_size;
    }

    float a[4];
    a[0] =
        a_table[int_pos_plus1] -
        a_table[int_pos] -
        a_table[int_pos_minus2] +
        a_table[int_pos_minus1];
    a[1] =
        a_table[int_pos_minus2] -
        a_table[int_pos_minus1] -
        a[0];
    a[2] =
        a_table[int_pos] -
        a_table[int_pos_minus2];
    a[3] = a_table[int_pos_minus1];

    return a[0] * mu * mu2 + a[1] * mu2 + a[2] * mu + a[3];
}

/* inline float f_cubic_interpolate_ptr_wrap(
 * float * a_table,
 * float a_ptr,
 * t_cubic_interpolater * a_lin)
 *
 * This method uses a pointer instead of an array the float* must be
 * malloc'd to (sizeof(float) * a_table_size)
 *
 * THIS DOES NOT CHECK THAT YOU PROVIDED A VALID POSITION
 */

inline float f_cubic_interpolate_ptr(float * a_table, float a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus1 = (int_pos) + 1;
    int int_pos_minus1 = (int_pos) - 1;
    int int_pos_minus2 = (int_pos) - 2;

#ifdef PYDAW_NO_HARDWARE
    // Check this when run with no hardware, but otherwise save the CPU.
    // Anything sending a position to this should already know that the
    // position is valid.
    assert(int_pos_minus1 >= 0);
    assert(int_pos_minus2 >= 0);
#endif

    float mu = a_ptr - (float)int_pos;

    float mu2 = (mu) * (mu);
    float a0 = a_table[int_pos_plus1] - a_table[int_pos] -
            a_table[int_pos_minus2] + a_table[int_pos_minus1];
    float a1 = a_table[int_pos_minus2] -
            a_table[int_pos_minus1] - a0;
    float a2 = a_table[int_pos] - a_table[int_pos_minus2];
    float a3 = a_table[int_pos_minus1];

    return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3);
}


/* inline float f_cubic_interpolate_ptr_ifh(
 * float * a_table,
 * int a_table_size,
 * int a_whole_number,
 * float a_frac,
 * t_lin_interpolater * a_lin)
 *
 * For use with the read_head type in Euphoria Sampler
 */
float f_cubic_interpolate_ptr_ifh(float * a_table, int a_whole_number,
        float a_frac)
{
    int int_pos = a_whole_number;
    int int_pos_plus1 = (int_pos) + 1;
    int int_pos_minus1 = (int_pos) - 1;
    int int_pos_minus2 = (int_pos) - 2;

    float mu = a_frac;

    float mu2 = (mu) * (mu);
    float a0 = a_table[int_pos_plus1] - a_table[int_pos] -
            a_table[int_pos_minus2] + a_table[int_pos_minus1];
    float a1 = a_table[int_pos_minus2] -
            a_table[int_pos_minus1] - a0;
    float a2 = a_table[int_pos] - a_table[int_pos_minus2];
    float a3 = a_table[int_pos_minus1];

    return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3);
}

#endif	/* INTERPOLATE_CUBIC_H */

