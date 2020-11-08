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
#ifndef SAMPLE_AND_HOLD_H
#define	SAMPLE_AND_HOLD_H

#include "../../lib/pitch_core.h"
#include "../../lib/lmalloc.h"
#include "../signal_routing/audio_xfade.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT output0, output1, hold0, hold1;
    int hold_count, hold_counter;
    MKFLT last_pitch, last_wet, sr;
    t_audio_xfade xfade;
} t_sah_sample_and_hold;

t_sah_sample_and_hold * g_sah_sample_and_hold_get(MKFLT);
void v_sah_sample_and_hold_set(t_sah_sample_and_hold*, MKFLT, MKFLT);
void v_sah_sample_and_hold_run(t_sah_sample_and_hold*, MKFLT, MKFLT);
void v_sah_free(t_sah_sample_and_hold*);


void g_sah_init(t_sah_sample_and_hold * f_result, MKFLT a_sr)
{
    f_result->hold_count = 1;
    f_result->hold_counter = 0;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->hold0 = 0.0f;
    f_result->hold1 = 0.0f;
    f_result->last_pitch = -99.999f;
    f_result->sr = a_sr;
    f_result->last_wet = -99.00088f;
    g_axf_init(&f_result->xfade, -3.0f);
}

t_sah_sample_and_hold * g_sah_sample_and_hold_get(MKFLT a_sr)
{
    t_sah_sample_and_hold * f_result;

    lmalloc((void**)&f_result, sizeof(t_sah_sample_and_hold));
    g_sah_init(f_result, a_sr);
    return f_result;
}

void v_sah_sample_and_hold_set(t_sah_sample_and_hold* a_sah, MKFLT a_pitch,
        MKFLT a_wet)
{
    if(a_sah->last_pitch != a_pitch)
    {
        a_sah->last_pitch = a_pitch;
        a_sah->hold_count =
            (int)(a_sah->sr / f_pit_midi_note_to_hz_fast(a_pitch));
    }

    if(a_sah->last_wet != a_wet)
    {
        a_sah->last_wet = a_wet;
        v_axf_set_xfade(&a_sah->xfade, a_wet);
    }
}

void v_sah_sample_and_hold_run(t_sah_sample_and_hold* a_sah,
        MKFLT a_in0, MKFLT a_in1)
{
    a_sah->output0 = f_axf_run_xfade(&a_sah->xfade, a_in0, a_sah->hold0);
    a_sah->output1 = f_axf_run_xfade(&a_sah->xfade, a_in1, a_sah->hold1);

    ++a_sah->hold_counter;

    if(a_sah->hold_counter >= a_sah->hold_count)
    {
        a_sah->hold_counter = 0;
        a_sah->hold0 = a_in0;
        a_sah->hold1 = a_in1;
    }
}

#ifdef	__cplusplus
}
#endif

#endif	/* SAMPLE_AND_HOLD_H */

