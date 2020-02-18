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

#ifndef SATURATOR_H
#define	SATURATOR_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/lms_math.h"
#include <math.h>

typedef struct st_sat_saturator
{
    float output0;
    float output1;
    float a;
    float b;
    float amount;
    float last_ingain;
    float last_outgain;
    float ingain_lin;
    float outgain_lin;
}t_sat_saturator;

t_sat_saturator * g_sat_get();
inline void v_sat_set(t_sat_saturator*,float,float,float);
inline void v_sat_run(t_sat_saturator*,float,float);
void v_sat_free(t_sat_saturator*);

void v_sat_free(t_sat_saturator * a_sat)
{
    free(a_sat);
}

inline void v_sat_set(t_sat_saturator* a_sat, float a_ingain, float a_amt,
        float a_outgain)
{
    if(a_ingain != (a_sat->last_ingain))
    {
        a_sat->last_ingain = a_ingain;
        a_sat->ingain_lin = f_db_to_linear_fast(a_ingain);
    }

    if(a_amt != (a_sat->amount))
    {
        a_sat->a=(a_amt*0.005)*3.141592f;
        a_sat->b = 1.0f / (sin((a_amt*0.005) * 3.141592f));
        a_sat->amount = a_amt;
    }

    if(a_outgain != (a_sat->last_outgain))
    {
        a_sat->last_outgain = a_outgain;
        a_sat->outgain_lin = f_db_to_linear_fast(a_outgain);
    }
}

inline void v_sat_run(t_sat_saturator* a_sat, float a_in0, float a_in1)
{
    a_sat->output0 = f_lms_min(
        f_lms_max(
        sin(
        f_lms_max(
        f_lms_min((a_in0 * (a_sat->ingain_lin)), 1.0f), -1.0f) * (a_sat->a))
        * (a_sat->b) ,-1.0f) ,1.0f) * (a_sat->outgain_lin);

    a_sat->output1 = f_lms_min(
        f_lms_max(
        sin(
        f_lms_max(
        f_lms_min((a_in1 * (a_sat->ingain_lin)), 1.0f), -1.0f) * (a_sat->a))
        * (a_sat->b) ,-1.0f) ,1.0f) * (a_sat->outgain_lin);
}

void g_sat_init(t_sat_saturator * f_result)
{
    f_result->a = 0.0f;
    f_result->b = 0.0f;
    f_result->amount = 1.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->ingain_lin = 1.0f;
    f_result->outgain_lin = 1.0f;
    f_result->last_ingain = 12345.0f;
    f_result->last_outgain = 12345.0f;
}


#ifdef	__cplusplus
}
#endif

#endif	/* SATURATOR_H */

