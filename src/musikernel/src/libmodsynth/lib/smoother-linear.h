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

#ifndef SMOOTHER_LINEAR_H
#define	SMOOTHER_LINEAR_H

#include "math.h"
#include "lmalloc.h"

/*Comment this out when compiling for a release, as it will waste a lot of CPU*/
//#define SML_DEBUG_MODE

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT rate;
    MKFLT last_value;
    MKFLT sample_rate;
    MKFLT sr_recip;

#ifdef SML_DEBUG_MODE
    int debug_counter;
#endif
}t_smoother_linear;

t_smoother_linear * g_sml_get_smoother_linear(MKFLT, MKFLT, MKFLT, MKFLT);
inline void v_sml_run(t_smoother_linear * a_smoother, MKFLT);

#ifdef	__cplusplus
}
#endif


void g_sml_init(t_smoother_linear * f_result, MKFLT a_sample_rate,
        MKFLT a_high, MKFLT a_low, MKFLT a_time_in_seconds)
{
    assert(a_high > a_low);
    f_result->last_value = (((a_high - a_low) * .5f) + a_low);

    /*Rate is the time it would take to complete if the knob was all
     * the way counter-clockwise, and then instantly moved all the
     * way clockwise*/
    f_result->rate = (((a_high - a_low ) / a_time_in_seconds) / a_sample_rate);

    f_result->sample_rate = a_sample_rate;
    f_result->sr_recip = 1.0f / a_sample_rate;
}

/* t_smoother_linear * g_sml_get_smoother_linear(
 * MKFLT a_sample_rate,
 * MKFLT a_high, //The high value of the control
 * MKFLT a_low,  //The low value of the control
 * MKFLT a_time_in_seconds)
 *
 * There's not much good reason to change this while the synth is running
 * for controls, so you should only set it here.
 * If using this for glide or other things that must be smoothed
 * dynamically, you can use the set method below
 */
t_smoother_linear * g_sml_get_smoother_linear(MKFLT a_sample_rate,
        MKFLT a_high, MKFLT a_low, MKFLT a_time_in_seconds)
{
    t_smoother_linear * f_result;

    lmalloc((void**)&f_result, sizeof(t_smoother_linear));

    g_sml_init(f_result, a_sample_rate, a_high, a_low, a_time_in_seconds);

#ifdef SML_DEBUG_MODE
    f_result->debug_counter = 0;
#endif

    return f_result;
}


/* inline void v_sml_run(
 * t_smoother_linear * a_smoother,
 * MKFLT a_current_value) //the current control value you wish to smooth
 *
 * smoother->last_value will be the smoothed value
 */
inline void v_sml_run(t_smoother_linear * a_smoother, MKFLT a_current_value)
{
    /*Evaluated first because most controls won't be moving most of the time,
     * should consume the fewest cycles*/
    if((a_smoother->last_value) == a_current_value)
    {
        //Do nothing
    }
    /*This does waste CPU while knobs are being moved, but it will effectively
     *  kill the knobs processing once it does reach it's destination value*/
    /*Moving up*/
    else if(((a_current_value > (a_smoother->last_value)) &&
            (a_current_value - (a_smoother->last_value) <= (a_smoother->rate)))
            /*Moving down*/
            || ((a_current_value < (a_smoother->last_value)) &&
            ((a_smoother->last_value) - a_current_value <= (a_smoother->rate))))
    {
        a_smoother->last_value = a_current_value;
    }

    /*Moving down*/
    else if(a_current_value > (a_smoother->last_value))
    {
        a_smoother->last_value = (a_smoother->last_value) + (a_smoother->rate);
    }

    /*Moving up*/
    else
    {
        a_smoother->last_value = (a_smoother->last_value) - (a_smoother->rate);
    }
}


#endif	/* SMOOTHER_LINEAR_H */

