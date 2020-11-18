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

#ifndef FOLDBACK_H
#define	FOLDBACK_H

#include <math.h>
#include "../../lib/amp.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT thresh, thresh_db, gain, gain_db, output[2];
} t_fbk_foldback;


#ifdef	__cplusplus
}
#endif

void g_fbk_init(t_fbk_foldback * self)
{
    self->output[0] = 0.0f;
    self->output[1] = 0.0f;
    self->thresh = 1.0f;
    self->thresh_db = 0.0f;
    self->gain = 1.0f;
    self->gain_db = 0.0f;
}

void v_fbk_set(t_fbk_foldback * self, MKFLT a_thresh_db, MKFLT a_gain_db)
{
    if(self->gain_db != a_gain_db)
    {
        self->gain_db = a_gain_db;
        self->gain = f_db_to_linear_fast(a_gain_db);
    }

    if(self->thresh_db != a_thresh_db)
    {
        self->thresh_db = a_thresh_db;
        self->thresh = f_db_to_linear_fast(a_thresh_db);
    }
}

void v_fbk_run(t_fbk_foldback * self, MKFLT a_input0, MKFLT a_input1)
{
    a_input0 *= self->gain;
    a_input1 *= self->gain;

    MKFLT f_arr[2] = {a_input0, a_input1};
    int f_i;

    for(f_i = 0; f_i < 2; ++f_i)
    {
        MKFLT f_input = f_arr[f_i];
        if(f_input > 0.0f)
        {
            if(f_input > self->thresh)
            {
                f_input = self->thresh - (f_input - self->thresh);
                if(f_input < 0.0f)
                {
                    f_input = 0.0f;
                }
            }
            self->output[f_i] = f_input;
        }
        else
        {
            f_input *= -1.0f;
            if(f_input > self->thresh)
            {
                f_input = self->thresh - (f_input - self->thresh);
                if(f_input < 0.0f)
                {
                    f_input = 0.0f;
                }
            }
            self->output[f_i] = f_input * -1.0f;
        }
    }
}

MKFLT f_fbk_mono(MKFLT a_val)
{
    if(a_val > 1.0f)
    {
        return 1.0 - fmodf(a_val, 1.0f);
    }
    else if(a_val < -1.0f)
    {
        return fmodf(a_val, 1.0f);
    }
    else
    {
        return a_val;
    }
}

#endif	/* FOLDBACK_H */

