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

#ifndef RING_MOD_H
#define	RING_MOD_H

#include "../oscillator/osc_simple.h"
#include "../signal_routing/audio_xfade.h"
#include "../../lib/lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT pitch;
    MKFLT last_wet;
    MKFLT output0, output1;
    t_osc_simple_unison osc;
    MKFLT osc_output;
    t_audio_xfade xfade;
}t_rmd_ring_mod;

t_rmd_ring_mod * g_rmd_ring_mod_get(MKFLT);
void v_rmd_ring_mod_set(t_rmd_ring_mod*, MKFLT, MKFLT);
void v_rmd_ring_mod_run(t_rmd_ring_mod*, MKFLT, MKFLT);


void g_rmd_init(t_rmd_ring_mod * f_result, MKFLT a_sr)
{
    g_osc_init_osc_simple_single(&f_result->osc, a_sr);
    v_osc_set_simple_osc_unison_type(&f_result->osc, 3);
    v_osc_set_uni_voice_count(&f_result->osc, 1);
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->last_wet = -110.0f;
    f_result->pitch = -99.99f;
    f_result->osc_output = 0.0f;
    g_axf_init(&f_result->xfade, 0.5f);
}

t_rmd_ring_mod * g_rmd_ring_mod_get(MKFLT a_sr)
{
    t_rmd_ring_mod * f_result;
    lmalloc((void**)&f_result, sizeof(t_rmd_ring_mod));
    g_rmd_init(f_result, a_sr);
    return f_result;
}

void v_rmd_ring_mod_set(t_rmd_ring_mod* a_rmd, MKFLT a_pitch, MKFLT a_wet)
{
    if(a_rmd->last_wet != a_wet)
    {
        a_rmd->last_wet = a_wet;
        v_axf_set_xfade(&a_rmd->xfade, a_wet);
    }

    if(a_rmd->pitch != a_pitch)
    {
        a_rmd->pitch = a_pitch;
        v_osc_set_unison_pitch(&a_rmd->osc, 0.0f, a_pitch);
    }
}

void v_rmd_ring_mod_run(t_rmd_ring_mod* a_rmd, MKFLT a_input0, MKFLT a_input1)
{
    a_rmd->osc_output = f_osc_run_unison_osc(&a_rmd->osc);

    a_rmd->output0 = f_axf_run_xfade(&a_rmd->xfade, a_input0,
            (a_input0 * (a_rmd->osc_output)));
    a_rmd->output1 = f_axf_run_xfade(&a_rmd->xfade, a_input1,
            (a_input1 * (a_rmd->osc_output)));
}


//f_get_sine



#ifdef	__cplusplus
}
#endif

#endif	/* RING_MOD_H */

