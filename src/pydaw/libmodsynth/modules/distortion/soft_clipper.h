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

#ifndef SOFT_CLIPPER_H
#define	SOFT_CLIPPER_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/amp.h"

typedef struct st_scl_soft_clipper
{
    MKFLT threshold_db;
    MKFLT threshold_linear, threshold_linear_neg;
    MKFLT amount;
    MKFLT output0;
    MKFLT output1;
    MKFLT temp;
    t_amp * amp_ptr;
}t_soft_clipper;

void v_scl_set(t_soft_clipper*,MKFLT,MKFLT);
void v_scl_run(t_soft_clipper*,MKFLT,MKFLT);
t_soft_clipper * g_scl_get();

void v_scl_set(t_soft_clipper* a_scl, MKFLT a_threshold_db, MKFLT a_amount)
{
    if(a_threshold_db != (a_scl->threshold_db))
    {
        a_scl->threshold_db = a_threshold_db;
        a_scl->threshold_linear =
                f_db_to_linear_fast(a_threshold_db, a_scl->amp_ptr);
        a_scl->threshold_linear_neg = (a_scl->threshold_linear) * -1.0f;
    }

    a_scl->amount = a_amount;
}

void v_scl_run(t_soft_clipper* a_scl,MKFLT a_in0, MKFLT a_in1)
{
    if(a_in0 > (a_scl->threshold_linear))
    {
        a_scl->temp = a_in0 - (a_scl->threshold_linear);
        a_scl->output0 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear);
    }
    else if(a_in0 < (a_scl->threshold_linear_neg))
    {
        a_scl->temp = a_in0 - (a_scl->threshold_linear_neg);
        a_scl->output0 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear_neg);
    }


    if(a_in1 > (a_scl->threshold_linear))
    {
        a_scl->temp = a_in1 - (a_scl->threshold_linear);
        a_scl->output1 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear);
    }
    else if(a_in1 < (a_scl->threshold_linear_neg))
    {
        a_scl->temp = a_in1 - (a_scl->threshold_linear_neg);
        a_scl->output1 =
            ((a_scl->temp) * (a_scl->amount)) + (a_scl->threshold_linear_neg);
    }
}

t_soft_clipper * g_scl_get()
{
    t_soft_clipper * f_result = (t_soft_clipper*)malloc(sizeof(t_soft_clipper));

    f_result->amount = 1.0f;
    f_result->amp_ptr = g_amp_get();
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->temp = 0.0f;
    f_result->threshold_db = 0.0f;
    f_result->threshold_linear = 1.0f;
    f_result->threshold_linear_neg = -1.0f;

    return f_result;
}

#ifdef	__cplusplus
}
#endif

#endif	/* SOFT_CLIPPER_H */

