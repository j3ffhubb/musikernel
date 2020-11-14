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

#ifndef AMP_AND_PANNER_H
#define	AMP_AND_PANNER_H

#include "../../lib/amp.h"
#include "../../lib/lms_math.h"
#include "../../lib/fast_sine.h"
#include "../../lib/lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct st_amp_and_panner
{
    MKFLT amp_db;
    MKFLT amp_linear;
    MKFLT pan; //0 to 1
    MKFLT amp_linear0;
    MKFLT amp_linear1;
    MKFLT output0;
    MKFLT output1;
}t_amp_and_panner;

void v_app_set(t_amp_and_panner*,MKFLT,MKFLT);
void v_app_run(t_amp_and_panner*,MKFLT,MKFLT);
t_amp_and_panner * g_app_get();

void v_app_set(t_amp_and_panner* a_app,MKFLT a_db,MKFLT a_pan)
{
    a_app->amp_db = a_db;
    a_app->pan = a_pan;

    a_app->amp_linear = f_db_to_linear_fast(a_db);

    a_app->amp_linear0 =
        (f_sine_fast_run(((a_pan * .5f) + 0.25f)) * 0.5f + 1.0f)
            * (a_app->amp_linear);
    a_app->amp_linear1 =
        (f_sine_fast_run((0.75f - (a_pan * 0.5f))) * 0.5f + 1.0f)
            * (a_app->amp_linear);
}

void v_app_run(t_amp_and_panner* a_app, MKFLT a_in0, MKFLT a_in1)
{
    a_app->output0 = a_in0 * (a_app->amp_linear0);
    a_app->output1 = a_in1 * (a_app->amp_linear1);
}

void v_app_run_monofier(t_amp_and_panner* a_app, MKFLT a_in0, MKFLT a_in1)
{
    v_app_run(a_app, a_in0, a_in1);
    a_app->output0 = a_app->output0 + a_app->output1;
    a_app->output1 = a_app->output0;
}

void g_app_init(t_amp_and_panner * f_result)
{
    f_result->amp_db = 0.0f;
    f_result->pan = 0.0f;
    f_result->amp_linear0 = 1.0f;
    f_result->amp_linear1 = 1.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
}

t_amp_and_panner * g_app_get()
{
    t_amp_and_panner * f_result;

    lmalloc((void**)&f_result, sizeof(t_amp_and_panner));
    g_app_init(f_result);

    return f_result;
}

void v_app_free(t_amp_and_panner * a_app)
{
    free(a_app);
}

#ifdef	__cplusplus
}
#endif

#endif	/* AMP_AND_PANNER_H */

