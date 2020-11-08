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

#ifndef LFO_SIMPLE_H
#define	LFO_SIMPLE_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "osc_simple.h"
#include "../../lib/lmalloc.h"
#include "../../lib/osc_core.h"

typedef struct st_lfs_lfo
{
    MKFLT inc, sr, sr_recip, output;
    t_osc_core osc_core;
    fp_get_osc_func_ptr osc_ptr;
}t_lfs_lfo;

inline void v_lfs_sync(t_lfs_lfo *,MKFLT,int);
inline void v_lfs_set(t_lfs_lfo *, MKFLT);
inline void v_lfs_run(t_lfs_lfo *);
t_lfs_lfo * g_lfs_get(MKFLT);
void v_lfs_free(t_lfs_lfo * );

/* inline void v_lfs_sync(
 * t_lfs_lfo * a_lfs,
 * MKFLT a_phase,  //the phase to resync to.  Range:  0 to .9999
 * int a_type)  //The type of LFO.  See types below
 *
 * Types:
 * 0 : Off
 * 1 : Sine
 * 2 : Triangle
 */
inline void v_lfs_sync(t_lfs_lfo * a_lfs, MKFLT a_phase, int a_type)
{
    a_lfs->osc_core.output = a_phase;

    switch(a_type)
    {
        case 0:
            a_lfs->osc_ptr = f_get_osc_off;
            break;
        case 1:
            a_lfs->osc_ptr = f_get_sine;
            break;
        case 2:
            a_lfs->osc_ptr = f_get_triangle;
            //So that it will be at 0 to begin with
            a_lfs->osc_core.output = 0.5f;
            break;
    }
}


/* void v_osc_set_hz(
 * t_lfs_lfo * a_lfs_ptr,
 * MKFLT a_hz)  //the pitch of the oscillator in hz, typically 0.1 to 10000
 *
 * For setting LFO frequency.
 */
inline void v_lfs_set(t_lfs_lfo * a_lfs_ptr, MKFLT a_hz)
{
    a_lfs_ptr->inc =  a_hz * a_lfs_ptr->sr_recip;
}

/* inline void v_lfs_run(t_lfs_lfo *)
 */
inline void v_lfs_run(t_lfs_lfo * a_lfs)
{
    v_run_osc(&a_lfs->osc_core, (a_lfs->inc));
    a_lfs->output = a_lfs->osc_ptr(&a_lfs->osc_core);
}

void g_lfs_init(t_lfs_lfo * f_result, MKFLT a_sr)
{
    f_result->inc = 0.0f;
    g_init_osc_core(&f_result->osc_core);
    f_result->osc_ptr = f_get_osc_off;
    f_result->output = 0.0f;
    f_result->sr = a_sr;
    f_result->sr_recip = 1.0f / a_sr;
}

t_lfs_lfo * g_lfs_get(MKFLT a_sr)
{
    t_lfs_lfo * f_result;
    lmalloc((void**)&f_result, sizeof(t_lfs_lfo));
    g_lfs_init(f_result, a_sr);
    return f_result;
}

void v_lfs_free(t_lfs_lfo * a_lfs)
{
    free(a_lfs);
}

#ifdef	__cplusplus
}
#endif

#endif	/* LFO_SIMPLE_H */

