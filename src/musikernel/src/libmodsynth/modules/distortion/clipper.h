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

#ifndef CLIPPER_H
#define	CLIPPER_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/amp.h"
#include "../../lib/lmalloc.h"

//#define CLP_DEBUG_MODE

typedef struct st_clipper
{
    MKFLT clip_high, clip_low, input_gain_linear, clip_db, in_db, result;
#ifdef CLP_DEBUG_MODE
    int debug_counter;
#endif
}t_clipper;

/*Set the values of a clipper struct symmetrically,
 * ie: value of .75 clips at .75 and -.75*/
void v_clp_set_clip_sym(t_clipper *, MKFLT);
void v_clp_set_in_gain(t_clipper *, MKFLT);
t_clipper * g_clp_get_clipper();
void v_clp_free(t_clipper *);
inline MKFLT f_clp_clip(t_clipper*, MKFLT);

/*v_clp_set_clip_sym(
 * t_clipper*,
 * MKFLT a_db //Threshold to clip at, in decibel,
 * ie:  -6db = clipping at .5 and -.5
 * )
 */
void v_clp_set_clip_sym(t_clipper * a_clp, MKFLT a_db)
{
    /*Already set, don't set again*/
    if(a_db == (a_clp->clip_db))
        return;

    a_clp->clip_db = a_db;

    MKFLT f_value = f_db_to_linear_fast(a_db);

#ifdef CLP_DEBUG_MODE
        printf("Clipper value == %f", f_value);
#endif

    a_clp->clip_high = f_value;
    a_clp->clip_low = (f_value * -1.0f);
}

/*void v_clp_set_in_gain(
 * t_clipper*,
 * MKFLT a_db   //gain in dB to apply to the input signal before clipping it,
 * usually a value between 0 and 36
 * )
 */
void v_clp_set_in_gain(t_clipper * a_clp, MKFLT a_db)
{
    if((a_clp->in_db) != a_db)
    {
        a_clp->in_db = a_db;
        a_clp->input_gain_linear = f_db_to_linear(a_db);
    }
}

void g_clp_init(t_clipper * f_result)
{
    f_result->clip_high = 1.0f;
    f_result->clip_low = -1.0f;
    f_result->input_gain_linear = 1.0f;
    f_result->in_db = 0.0f;
    f_result->result = 0.0f;
    f_result->clip_db = 7654567.0f;
}

t_clipper * g_clp_get_clipper()
{
    t_clipper * f_result;

    lmalloc((void**)&f_result, sizeof(t_clipper));
    g_clp_init(f_result);
    return f_result;
};

/* inline MKFLT f_clp_clip(
 * t_clipper *,
 * MKFLT a_input  //value to be clipped
 * )
 *
 * This function performs the actual clipping, and returns a MKFLT
 */
inline MKFLT f_clp_clip(t_clipper * a_clp, MKFLT a_input)
{
    a_clp->result = a_input * (a_clp->input_gain_linear);

    if(a_clp->result > (a_clp->clip_high))
        a_clp->result = (a_clp->clip_high);
    else if(a_clp->result < (a_clp->clip_low))
        a_clp->result = (a_clp->clip_low);

    return (a_clp->result);
}


void v_clp_free(t_clipper * a_clp)
{
    free(a_clp);
}

#ifdef	__cplusplus
}
#endif

#endif	/* CLIPPER_H */

