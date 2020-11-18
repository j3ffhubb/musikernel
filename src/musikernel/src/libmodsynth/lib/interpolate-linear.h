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

#ifndef INTERPOLATE_LINEAR_H
#define	INTERPOLATE_LINEAR_H

#include "lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

inline MKFLT f_linear_interpolate(MKFLT, MKFLT, MKFLT);
MKFLT f_linear_interpolate_ptr_wrap(MKFLT*, int, MKFLT);
inline MKFLT f_linear_interpolate_ptr(MKFLT*, MKFLT);
inline MKFLT f_linear_interpolate_ptr_ifh(MKFLT * a_table, int a_whole_number,
        MKFLT a_frac);

#ifdef	__cplusplus
}
#endif


/* inline MKFLT f_linear_interpolate(
 * MKFLT a_a, //item 0
 * MKFLT a_b, //item 1
 * MKFLT a_position)  //position between the 2, range:  0 to 1
 */
inline MKFLT f_linear_interpolate(MKFLT a_a, MKFLT a_b, MKFLT a_pos)
{
    return ((1.0f - a_pos) * a_a) + (a_pos * a_b);
}


/* MKFLT f_linear_interpolate_ptr_wrap(
 * MKFLT * a_table,
 * int a_table_size,
 * MKFLT a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the MKFLT* must be malloc'd
 * to (sizeof(MKFLT) * a_table_size)
 */
MKFLT f_linear_interpolate_ptr_wrap(MKFLT * a_table, int a_table_size,
        MKFLT a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    if(unlikely(int_pos >= a_table_size))
    {
        int_pos -= a_table_size;
    }

    if(unlikely(int_pos_plus_1 >= a_table_size))
    {
        int_pos_plus_1 -= a_table_size;
    }

    if(unlikely(int_pos < 0))
    {
        int_pos += a_table_size;
    }

    if(unlikely(int_pos_plus_1 < 0))
    {
        int_pos_plus_1 += a_table_size;
    }

    MKFLT pos = a_ptr - int_pos;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

/* inline MKFLT f_linear_interpolate_ptr_wrap(
 * MKFLT * a_table,
 * MKFLT a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the MKFLT* must be malloc'd
 * to (sizeof(MKFLT) * a_table_size)
 *
 * THIS DOES NOT CHECK THAT YOU PROVIDED A VALID POSITION
 */
inline MKFLT f_linear_interpolate_ptr(MKFLT * a_table, MKFLT a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    MKFLT pos = a_ptr - int_pos;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

/* inline MKFLT f_linear_interpolate_ptr_ifh(
 * MKFLT * a_table,
 * int a_table_size,
 * int a_whole_number,
 * MKFLT a_frac,
 * )
 *
 * For use with the read_head type in Euphoria Sampler
 */
inline MKFLT f_linear_interpolate_ptr_ifh(MKFLT * a_table, int a_whole_number,
        MKFLT a_frac)
{
    int int_pos = a_whole_number;
    int int_pos_plus_1 = int_pos + 1;

    MKFLT pos = a_frac;

    return f_linear_interpolate(a_table[int_pos], a_table[int_pos_plus_1], pos);
}

#endif	/* INTERPOLATE_LINEAR_H */

