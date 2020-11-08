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

#ifndef LMS_MATH_H
#define	LMS_MATH_H

#include "interpolate-linear.h"

#ifdef	__cplusplus
extern "C" {
#endif

inline MKFLT f_lms_abs(MKFLT);
inline MKFLT f_lms_max(MKFLT,MKFLT);
inline MKFLT f_lms_min(MKFLT,MKFLT);
inline MKFLT f_lms_floor(MKFLT,MKFLT);
inline MKFLT f_lms_ceiling(MKFLT,MKFLT);
inline MKFLT f_lms_sqrt(MKFLT);

#ifdef	__cplusplus
}
#endif


/* inline MKFLT f_lms_abs(MKFLT a_input)
 *
 * Return the absolute value of a MKFLT.  Use this instead of fabs from
 * math.h, it's much faster
 */
inline MKFLT f_lms_abs(MKFLT a_input)
{
    if(a_input > 0.0f)
    {
        return a_input;
    }
    else
    {
        return a_input * -1.0f;
    }
}

/* inline MKFLT f_lms_max(MKFLT a_1,MKFLT a_2)
 *
 * Return the larger of 2 MKFLTs
 */
inline MKFLT f_lms_max(MKFLT a_1,MKFLT a_2)
{
    if(a_1 > a_2)
    {
        return a_1;
    }
    else
    {
        return a_2;
    }
}

/* inline MKFLT f_lms_max(MKFLT a_1,MKFLT a_2)
 *
 * Return the lesser of 2 MKFLTs
 */
inline MKFLT f_lms_min(MKFLT a_1, MKFLT a_2)
{
    if(a_1 < a_2)
    {
        return a_1;
    }
    else
    {
        return a_2;
    }
}

/* inline MKFLT f_lms_floor(MKFLT a_input, MKFLT a_floor)
 *
 * Clips a value if less than a_floor
 */
inline MKFLT f_lms_floor(MKFLT a_input, MKFLT a_floor)
{
    if(a_input < a_floor)
    {
        return a_floor;
    }
    else
    {
        return a_input;
    }
}

/* inline MKFLT f_lms_ceiling(MKFLT a_input, MKFLT a_ceiling)
 *
 * Clips a value if more than a_ceiling
 */
inline MKFLT f_lms_ceiling(MKFLT a_input, MKFLT a_ceiling)
{
    if(a_input > a_ceiling)
    {
        return a_ceiling;
    }
    else
    {
        return a_input;
    }
}

#define arr_sqrt_count 401

__thread MKFLT arr_sqrt [arr_sqrt_count]
__attribute__((aligned(CACHE_LINE_SIZE))) = {
0.000000,0.100000,0.141421,0.173205,0.200000,0.223607,
0.244949,0.264575,0.282843,0.300000,0.316228,0.331662,
0.346410,0.360555,0.374166,0.387298,0.400000,0.412311,
0.424264,0.435890,0.447214,0.458258,0.469042,0.479583,
0.489898,0.500000,0.509902,0.519615,0.529150,0.538516,
0.547723,0.556776,0.565685,0.574456,0.583095,0.591608,
0.600000,0.608276,0.616441,0.624500,0.632456,0.640312,
0.648074,0.655744,0.663325,0.670820,0.678233,0.685565,
0.692820,0.700000,0.707107,0.714143,0.721110,0.728011,
0.734847,0.741620,0.748331,0.754983,0.761577,0.768115,
0.774597,0.781025,0.787401,0.793725,0.800000,0.806226,
0.812404,0.818535,0.824621,0.830662,0.836660,0.842615,
0.848528,0.854400,0.860233,0.866025,0.871780,0.877496,
0.883176,0.888819,0.894427,0.900000,0.905539,0.911043,
0.916515,0.921954,0.927362,0.932738,0.938083,0.943398,
0.948683,0.953939,0.959166,0.964365,0.969536,0.974679,
0.979796,0.984886,0.989949,0.994987,1.000000,1.004988,
1.009950,1.014889,1.019804,1.024695,1.029563,1.034408,
1.039230,1.044031,1.048809,1.053565,1.058301,1.063015,
1.067708,1.072381,1.077033,1.081665,1.086278,1.090871,
1.095445,1.100000,1.104536,1.109054,1.113553,1.118034,
1.122497,1.126943,1.131371,1.135782,1.140175,1.144552,
1.148913,1.153256,1.157584,1.161895,1.166190,1.170470,
1.174734,1.178983,1.183216,1.187434,1.191638,1.195826,
1.200000,1.204159,1.208305,1.212436,1.216553,1.220656,
1.224745,1.228821,1.232883,1.236932,1.240967,1.244990,
1.249000,1.252996,1.256981,1.260952,1.264911,1.268858,
1.272792,1.276715,1.280625,1.284523,1.288410,1.292285,
1.296148,1.300000,1.303840,1.307670,1.311488,1.315295,
1.319091,1.322876,1.326650,1.330413,1.334166,1.337909,
1.341641,1.345362,1.349074,1.352775,1.356466,1.360147,
1.363818,1.367479,1.371131,1.374773,1.378405,1.382027,
1.385641,1.389244,1.392839,1.396424,1.400000,1.403567,
1.407125,1.410674,1.414214,1.417745,1.421267,1.424781,
1.428286,1.431782,1.435270,1.438749,1.442221,1.445683,
1.449138,1.452584,1.456022,1.459452,1.462874,1.466288,
1.469694,1.473092,1.476482,1.479865,1.483240,1.486607,
1.489966,1.493318,1.496663,1.500000,1.503330,1.506652,
1.509967,1.513275,1.516575,1.519868,1.523155,1.526434,
1.529706,1.532971,1.536229,1.539480,1.542725,1.545962,
1.549193,1.552417,1.555635,1.558846,1.562050,1.565248,
1.568439,1.571623,1.574802,1.577973,1.581139,1.584298,
1.587451,1.590597,1.593738,1.596872,1.600000,1.603122,
1.606238,1.609348,1.612452,1.615549,1.618641,1.621727,
1.624808,1.627882,1.630951,1.634013,1.637071,1.640122,
1.643168,1.646208,1.649242,1.652271,1.655295,1.658312,
1.661325,1.664332,1.667333,1.670329,1.673320,1.676305,
1.679286,1.682260,1.685230,1.688194,1.691153,1.694107,
1.697056,1.700000,1.702939,1.705872,1.708801,1.711724,
1.714643,1.717556,1.720465,1.723369,1.726268,1.729162,
1.732051,1.734935,1.737815,1.740690,1.743560,1.746425,
1.749286,1.752142,1.754993,1.757840,1.760682,1.763519,
1.766352,1.769181,1.772005,1.774824,1.777639,1.780449,
1.783255,1.786057,1.788854,1.791647,1.794436,1.797220,
1.800000,1.802776,1.805547,1.808314,1.811077,1.813836,
1.816590,1.819341,1.822087,1.824829,1.827567,1.830301,
1.833030,1.835756,1.838478,1.841195,1.843909,1.846619,
1.849324,1.852026,1.854724,1.857418,1.860108,1.862794,
1.865476,1.868154,1.870829,1.873499,1.876166,1.878829,
1.881489,1.884144,1.886796,1.889444,1.892089,1.894730,
1.897367,1.900000,1.902630,1.905256,1.907878,1.910497,
1.913113,1.915724,1.918333,1.920937,1.923538,1.926136,
1.928730,1.931321,1.933908,1.936492,1.939072,1.941649,
1.944222,1.946792,1.949359,1.951922,1.954482,1.957039,
1.959592,1.962142,1.964688,1.967232,1.969772,1.972308,
1.974842,1.977372,1.979899,1.982423,1.984943,1.987461,
1.989975,1.992486,1.994994,1.997498,2.000000};

/* inline MKFLT f_lms_sqrt(MKFLT a_input)
 *
 * Calculate a square root using a fast table-based lookup.
 * The range is zero to 4
 */
inline MKFLT f_lms_sqrt(MKFLT a_input)
{
    return f_linear_interpolate_ptr(arr_sqrt, (a_input * 100.0f));
}



#endif	/* LMS_MATH_H */

