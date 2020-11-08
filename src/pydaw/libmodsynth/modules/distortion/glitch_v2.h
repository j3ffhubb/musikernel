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

#ifndef PYDAW_GLITCH_V2_H
#define	PYDAW_GLITCH_V2_H

#include "../../lib/interpolate-cubic.h"
#include "../../lib/pitch_core.h"
#include "../../lib/lmalloc.h"
#include "../modulation/adsr.h"
#include "../signal_routing/audio_xfade.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT * buffer;
    MKFLT read_head;
    int buffer_size, read_head_int, write_head, first_run;
    MKFLT last_time, last_pitch;
    int sample_count;
    MKFLT sr, sample_count_f;
    MKFLT rate;
    MKFLT output0, output1;
    t_pit_ratio pitch_ratio;
    t_audio_xfade xfade;
    t_adsr adsr;
}t_glc_glitch_v2;

void g_glc_glitch_v2_init(t_glc_glitch_v2*, MKFLT);
void v_glc_glitch_v2_set(t_glc_glitch_v2*, MKFLT, MKFLT);
void v_glc_glitch_v2_run(t_glc_glitch_v2*, MKFLT, MKFLT);

#ifdef	__cplusplus
}
#endif


void g_glc_glitch_v2_init(t_glc_glitch_v2 * f_result, MKFLT a_sr)
{
    f_result->buffer_size = (int)(a_sr * 0.25f);

    hpalloc((void**)&f_result->buffer,
        sizeof(MKFLT) * (f_result->buffer_size + 100));

    g_pit_ratio_init(&f_result->pitch_ratio);
    g_adsr_init(&f_result->adsr, a_sr);
    g_axf_init(&f_result->xfade, -3.0f);

    v_adsr_set_adsr(&f_result->adsr, 0.0f, 0.05f, 1.0f, 0.01f);

    int f_i = 0;

    while(f_i < f_result->buffer_size + 100)
    {
        f_result->buffer[f_i] = 0.0f;
        ++f_i;
    }

    f_result->read_head_int = 0;
    f_result->read_head = 0.0f;
    f_result->rate = 1.0f;
    f_result->write_head = 0;
    f_result->last_time = 654654.89f;
    f_result->last_pitch = 654654.89f;
    f_result->sample_count = 99;
    f_result->sample_count_f = 99.99f;
    f_result->sr = a_sr;
}

void v_glc_glitch_v2_set(t_glc_glitch_v2* a_glc, MKFLT a_time, MKFLT a_pitch)
{
    if(a_glc->last_time != a_time)
    {
        a_glc->last_time = a_time;
        a_glc->sample_count_f = ((a_glc->sr) * a_time);
        a_glc->sample_count = (int)a_glc->sample_count_f;

        if(a_glc->read_head >= a_glc->sample_count_f)
        {
            a_glc->read_head = 0.0f;
        }
    }

    if(a_glc->last_pitch != a_pitch)
    {
        a_glc->last_pitch = a_pitch;
        if(a_pitch == 0.0f)
        {
            a_glc->rate = 1.0f;
        }
        else if (a_pitch > 0.0f)
        {
            a_glc->rate = f_pit_midi_note_to_ratio_fast(
                0.0f, a_pitch, &a_glc->pitch_ratio);
        }
        else
        {
            a_glc->rate = f_pit_midi_note_to_ratio_fast(
                a_pitch * -1.0f, 0.0f, &a_glc->pitch_ratio);
        }

    }
}

inline void v_glc_glitch_v2_retrigger(t_glc_glitch_v2* a_glc)
{
    a_glc->read_head = 0.0f;
    a_glc->read_head_int = 0;
    a_glc->write_head = 0;
    a_glc->first_run = 1;
    v_adsr_retrigger(&a_glc->adsr);
}

inline void v_glc_glitch_v2_release(t_glc_glitch_v2* a_glc)
{
    v_adsr_release(&a_glc->adsr);
}

void v_glc_glitch_v2_run(t_glc_glitch_v2* a_glc, MKFLT a_input0, MKFLT a_input1)
{
    if(a_glc->write_head < a_glc->buffer_size)
    {
        a_glc->buffer[a_glc->write_head] = (a_input0 + a_input1) * 0.5f;
        ++a_glc->write_head;
    }

    v_adsr_run(&a_glc->adsr);

    if(a_glc->first_run)
    {
        a_glc->output0 = a_input0;
        a_glc->output1 = a_input1;

        ++a_glc->read_head_int;
        if(a_glc->read_head_int >= a_glc->sample_count)
        {
            a_glc->first_run = 0;
        }
    }
    else
    {
        MKFLT f_pos = a_glc->read_head;

        if(f_pos > (MKFLT)a_glc->write_head)
        {
            f_pos = (MKFLT)a_glc->write_head;
        }

        MKFLT f_output =
            f_cubic_interpolate_ptr_wrap(
                a_glc->buffer, a_glc->sample_count, a_glc->read_head);

        v_axf_set_xfade(&a_glc->xfade, a_glc->adsr.output);

        a_glc->output0 = f_axf_run_xfade(&a_glc->xfade, a_input0, f_output);
        a_glc->output1 = f_axf_run_xfade(&a_glc->xfade, a_input1, f_output);

        a_glc->read_head += a_glc->rate;
        if(a_glc->read_head >= a_glc->sample_count_f)
        {
            a_glc->read_head -= a_glc->sample_count_f;
        }
    }
}

#endif	/* PYDAW_GLITCH_V2_H */

