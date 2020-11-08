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


#ifndef RAMP_ENV_H
#define	RAMP_ENV_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/interpolate-cubic.h"
#include "../../lib/interpolate-linear.h"

typedef struct st_ramp_env
{
    MKFLT output;  //if == 1, the ramp can be considered finished running
    MKFLT output_multiplied;
    MKFLT ramp_time;
    MKFLT ramp_inc;
    MKFLT sr;
    MKFLT sr_recip;
    MKFLT output_multiplier;
    MKFLT curve;  //0.0-1.0, for the interpolator
    MKFLT last_curve;  //0.0-1.0, for the interpolator
    MKFLT curve_table[5];
}t_ramp_env;


inline void f_rmp_run_ramp(t_ramp_env*);
void v_rmp_retrigger(t_ramp_env*,MKFLT,MKFLT);
void v_rmp_retrigger_glide_t(t_ramp_env*,MKFLT,MKFLT,MKFLT);
void v_rmp_retrigger_glide_r(t_ramp_env*,MKFLT,MKFLT,MKFLT);
void v_rmp_set_time(t_ramp_env*,MKFLT);
t_ramp_env * g_rmp_get_ramp_env(MKFLT);



inline void f_rmp_run_ramp(t_ramp_env* a_rmp_ptr)
{
    if((a_rmp_ptr->output_multiplier) == 0.0f )
    {
        a_rmp_ptr->output_multiplied = 0.0f;
        return;
    }

    if((a_rmp_ptr->output) == 1.0f)
    {
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }

    a_rmp_ptr->output = (a_rmp_ptr->output) + (a_rmp_ptr->ramp_inc);

    if((a_rmp_ptr->output) >= 1.0f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }

    a_rmp_ptr->output_multiplied =
        (a_rmp_ptr->output) * (a_rmp_ptr->output_multiplier);
}


inline void f_rmp_run_ramp_curve(t_ramp_env* a_rmp_ptr)
{
    f_rmp_run_ramp(a_rmp_ptr);

    a_rmp_ptr->output_multiplied =
    f_cubic_interpolate_ptr(a_rmp_ptr->curve_table, 2.0f + a_rmp_ptr->output)
        * (a_rmp_ptr->output_multiplier);
}


/* void v_rmp_set_time(
 * t_ramp_env* a_rmp_ptr,
 * MKFLT a_time)  //time in seconds
 *
 * Set envelope time without retriggering the envelope
 */
void v_rmp_set_time(t_ramp_env* a_rmp_ptr,MKFLT a_time)
{
    a_rmp_ptr->ramp_time = a_time;

    if((a_rmp_ptr->ramp_time) <= .01f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }
}

/* void v_rmp_set_time(
 * t_ramp_env* a_rmp_ptr,
 * MKFLT a_time,  //time in seconds
 * MKFLT a_curve) // 0.0 to 1.0
 *
 * Retrigger when using with
 */
void v_rmp_retrigger_curve(t_ramp_env* a_rmp_ptr, MKFLT a_time, MKFLT a_multiplier, MKFLT a_curve)
{
    v_rmp_retrigger(a_rmp_ptr, a_time, a_multiplier);

    if(a_rmp_ptr->curve != a_curve)
    {
        a_rmp_ptr->curve_table[1] = f_linear_interpolate(0.0f, a_curve, 0.66666f);
        a_rmp_ptr->curve_table[2] = f_linear_interpolate(a_curve, 1.0f, 0.33333f);
        a_rmp_ptr->curve = a_curve;
    }
}


/*void v_rmp_retrigger(
 * t_ramp_env* a_rmp_ptr,
 * MKFLT a_time,
 * MKFLT a_multiplier)
 */
void v_rmp_retrigger(t_ramp_env* a_rmp_ptr, MKFLT a_time, MKFLT a_multiplier)
{
    a_rmp_ptr->output = 0.0f;
    a_rmp_ptr->ramp_time = a_time;
    a_rmp_ptr->output_multiplier = a_multiplier;

    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }

}

/*Glide with constant time in seconds*/
void v_rmp_retrigger_glide_t(t_ramp_env* a_rmp_ptr, MKFLT a_time, MKFLT a_current_note, MKFLT a_next_note)
{
    a_rmp_ptr->ramp_time = a_time;

    a_rmp_ptr->output_multiplier = a_next_note - a_current_note;

    /*Turn off if true*/
    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }

}

/*Glide with constant rate in seconds-per-octave*/
void v_rmp_retrigger_glide_r(t_ramp_env* a_rmp_ptr, MKFLT a_time, MKFLT a_current_note, MKFLT a_next_note)
{
    a_rmp_ptr->output = 0.0f;
    a_rmp_ptr->output_multiplier = a_next_note - a_current_note;
    a_rmp_ptr->ramp_time = a_time * (a_rmp_ptr->output_multiplier) * .083333f;

    /*Turn off if true*/
    if((a_rmp_ptr->ramp_time) <= .05f)
    {
        a_rmp_ptr->output = 1.0f;
        a_rmp_ptr->output_multiplied = (a_rmp_ptr->output_multiplier);
        return;
    }
    else
    {
        a_rmp_ptr->output = 0.0f;
        a_rmp_ptr->ramp_inc = (a_rmp_ptr->sr_recip) / (a_rmp_ptr->ramp_time);
    }
}

void g_rmp_init(t_ramp_env * f_result, MKFLT a_sr)
{
    f_result->sr = a_sr;
    f_result->sr_recip = 1.0f/a_sr;
    f_result->output_multiplied = 0.0f;
    f_result->output_multiplier = 1.0f;
    f_result->ramp_inc = .01f;
    f_result->ramp_time = .05f;
    f_result->output = 0.0f;
    f_result->curve = 1342.0f;
    f_result->last_curve = 422.4f;
    f_result->curve_table[0] = 0.0f;
    f_result->curve_table[1] = 0.3333f;
    f_result->curve_table[2] = 0.6666f;
    f_result->curve_table[3] = 1.0f;
    f_result->curve_table[4] = 1.0f;
}

/*t_ramp_env * g_rmp_get_ramp_env(
 * MKFLT a_sr  //sample rate
 * )
 */
t_ramp_env * g_rmp_get_ramp_env(MKFLT a_sr)
{
    t_ramp_env * f_result;
    lmalloc((void**)&f_result, sizeof(t_ramp_env));
    g_rmp_init(f_result, a_sr);
    return f_result;
}

#ifdef	__cplusplus
}
#endif

#endif	/* RAMP_ENV_H */

