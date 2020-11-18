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

#ifndef NOISE_H
#define	NOISE_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/lmalloc.h"
#include <stdlib.h>
#include <time.h>

typedef struct st_white_noise
{
    int array_count, read_head;
    MKFLT * sample_array;
    MKFLT b0,b1,b2,b3,b4,b5,b6;  //pink noise coefficients
}t_white_noise;

typedef MKFLT (*fp_noise_func_ptr)(t_white_noise*);

t_white_noise * g_get_white_noise(MKFLT);
inline MKFLT f_run_white_noise(t_white_noise *);
inline MKFLT f_run_pink_noise(t_white_noise *);
inline MKFLT f_run_noise_off(t_white_noise *);
inline fp_noise_func_ptr fp_get_noise_func_ptr(int);

fp_noise_func_ptr f_noise_func_ptr_arr[] =
{
    f_run_noise_off,
    f_run_white_noise,
    f_run_pink_noise,
    f_run_noise_off
};

inline fp_noise_func_ptr fp_get_noise_func_ptr(int a_index)
{
    return f_noise_func_ptr_arr[a_index];
}

static unsigned int seed_helper = 18;

void g_white_noise_init(t_white_noise * f_result, MKFLT a_sample_rate)
{
    time_t f_clock = time(NULL);
    srand(((unsigned)f_clock) + (seed_helper));

    seed_helper *= 2;
    f_result->array_count = (int)(a_sample_rate);

    f_result->read_head = 0;

    hpalloc((void**)&f_result->sample_array,
        sizeof(MKFLT) * f_result->array_count);

    f_result->b0 = f_result->b1 = f_result->b2 = f_result->b3 =
            f_result->b4 = f_result->b5 = f_result->b6 = 0.0f;


    int f_i = 0;
    double f_rand_recip = 1.0f / (double)RAND_MAX;

    while(f_i < f_result->array_count)
    {
        /*Mixing 3 random numbers together gives a more natural
         * sounding white noise, instead of a "brick" of noise,
         * as seen on an oscilloscope*/
        MKFLT f_sample1 = ((double)rand() * f_rand_recip) - 0.5f;
        MKFLT f_sample2 = ((double)rand() * f_rand_recip) - 0.5f;
        MKFLT f_sample3 = ((double)rand() * f_rand_recip) - 0.5f;

        f_result->sample_array[f_i] = (f_sample1 + f_sample2 + f_sample3) * .5f;
        f_i++;
    }
}

/* t_white_noise * g_get_white_noise(MKFLT a_sample_rate)
 */
t_white_noise * g_get_white_noise(MKFLT a_sample_rate)
{
    t_white_noise * f_result;
    hpalloc((void**)&f_result, sizeof(t_white_noise));
    g_white_noise_init(f_result, a_sample_rate);
    return f_result;
}

/* inline MKFLT f_run_white_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of white noise
 */
inline MKFLT f_run_white_noise(t_white_noise * a_w_noise)
{
    ++a_w_noise->read_head;

    if((a_w_noise->read_head) >= (a_w_noise->array_count))
    {
        a_w_noise->read_head = 0;
    }

    return a_w_noise->sample_array[(a_w_noise->read_head)];
}

/* inline MKFLT f_run_pink_noise(t_white_noise * a_w_noise)
 *
 * returns a single sample of pink noise
 */
inline MKFLT f_run_pink_noise(t_white_noise * a_w_noise)
{
    ++a_w_noise->read_head;

    if((a_w_noise->read_head) >= (a_w_noise->array_count))
    {
        a_w_noise->read_head = 0;
    }

    MKFLT f_white = a_w_noise->sample_array[(a_w_noise->read_head)];

    (a_w_noise->b0) = 0.99886f * (a_w_noise->b0) + f_white * 0.0555179f;
    (a_w_noise->b1) = 0.99332f * (a_w_noise->b1) + f_white * 0.0750759f;
    (a_w_noise->b2) = 0.96900f * (a_w_noise->b2) + f_white * 0.1538520f;
    (a_w_noise->b3) = 0.86650f * (a_w_noise->b3) + f_white * 0.3104856f;
    (a_w_noise->b4) = 0.55000f * (a_w_noise->b4) + f_white * 0.5329522f;
    (a_w_noise->b5) = -0.7616f * (a_w_noise->b5) - f_white * 0.0168980f;
    (a_w_noise->b6) = f_white * 0.115926f;
    return (a_w_noise->b0) + (a_w_noise->b1) + (a_w_noise->b2) + (a_w_noise->b3)
        + (a_w_noise->b4) + (a_w_noise->b5) + (a_w_noise->b6) + f_white *
            0.5362f;
}

inline MKFLT f_run_noise_off(t_white_noise * a_w_noise)
{
    return 0.0f;
}


#ifdef	__cplusplus
}
#endif

#endif	/* NOISE_H */

