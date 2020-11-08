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

#ifndef PYDAW_REVERB_H
#define	PYDAW_REVERB_H

#define PYDAW_REVERB_DIFFUSER_COUNT 5
#define PYDAW_REVERB_TAP_COUNT 12


#include "../../lib/amp.h"
#include "../../lib/lmalloc.h"
#include "../../lib/pitch_core.h"
#include "../filter/comb_filter.h"
#include "../filter/svf.h"
#include "../oscillator/lfo_simple.h"

#ifdef  __cplusplus
extern "C" {
#endif

typedef struct
{
    t_comb_filter tap;
    MKFLT pitch;
}t_rvb_tap;

typedef struct
{
    t_state_variable_filter diffuser;
    MKFLT pitch;
}t_rvb_diffuser;

typedef struct
{
    MKFLT output;
    MKFLT feedback;
    t_lfs_lfo lfo;
    t_state_variable_filter lp;
    t_state_variable_filter hp;
    MKFLT wet_linear;
    t_rvb_tap taps[PYDAW_REVERB_TAP_COUNT];
    t_rvb_diffuser diffusers[PYDAW_REVERB_DIFFUSER_COUNT];
    MKFLT * predelay_buffer;
    int predelay_counter;
    int predelay_size;
    MKFLT color;
    MKFLT wet;
    MKFLT time;
    MKFLT volume_factor;
    MKFLT last_predelay;
    MKFLT sr;
    MKFLT hp_cutoff;
} t_rvb_reverb;

t_rvb_reverb * g_rvb_reverb_get(MKFLT);
void v_rvb_reverb_set(t_rvb_reverb *, MKFLT, MKFLT, MKFLT, MKFLT, MKFLT);
inline void v_rvb_reverb_run(t_rvb_reverb *, MKFLT, MKFLT);


void v_rvb_reverb_set(t_rvb_reverb * self, MKFLT a_time, MKFLT a_wet,
        MKFLT a_color, MKFLT a_predelay, MKFLT a_hp_cutoff)
{
    if(unlikely(a_time != self->time))
    {
        int f_i;
        MKFLT f_base = 30.0f - (a_time * 25.0f);
        MKFLT f_factor = 1.4f + (a_time * 0.8f);

        self->feedback = a_time - 1.03f;
        v_lfs_set(&self->lfo, 1.0f - (a_time * 0.9f));

        for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
        {
            self->taps[f_i].pitch = f_base + (((MKFLT)f_i) * f_factor);
            v_cmb_set_all(&self->taps[f_i].tap, 0.0f, self->feedback,
                self->taps[f_i].pitch);
        }

        self->time = a_time;
    }

    if(unlikely(a_wet != self->wet))
    {
        self->wet = a_wet;
        self->wet_linear =  a_wet * (self->volume_factor);
    }

    if(unlikely(a_color != self->color))
    {
        self->color = a_color;
        v_svf_set_cutoff_base(&self->lp, a_color);
        v_svf_set_cutoff(&self->lp);
    }

    if(unlikely(self->last_predelay != a_predelay))
    {
        self->last_predelay = a_predelay;
        self->predelay_size = (int)(self->sr * a_predelay);
        if(self->predelay_counter >= self->predelay_size)
        {
            self->predelay_counter = 0;
        }
    }

    if(unlikely(self->hp_cutoff != a_hp_cutoff))
    {
        v_svf_set_cutoff_base(&self->hp, a_hp_cutoff);
        v_svf_set_cutoff(&self->hp);
        self->hp_cutoff = a_hp_cutoff;
    }
}

inline void v_rvb_reverb_run(t_rvb_reverb * self, MKFLT a_input0,
        MKFLT a_input1)
{
    int f_i;
    t_state_variable_filter * f_filter;
    t_comb_filter * f_comb;

    self->output *= 0.02f;
    v_lfs_run(&self->lfo);
    MKFLT f_lfo_diff = self->lfo.output * 2.0f;

    MKFLT f_tmp_sample = v_svf_run_2_pole_lp(&self->lp,
            (a_input0 + a_input1));
    f_tmp_sample = v_svf_run_2_pole_hp(&self->hp, f_tmp_sample);
    f_tmp_sample *= (self->wet_linear);

    for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
    {
        f_comb = &self->taps[f_i].tap;
        v_cmb_run(f_comb, f_tmp_sample);
        self->output += f_comb->output_sample;
    }

    for(f_i = 0; f_i < PYDAW_REVERB_DIFFUSER_COUNT; ++f_i)
    {
        f_filter = &self->diffusers[f_i].diffuser;
        v_svf_set_cutoff_base(f_filter,
            self->diffusers[f_i].pitch + f_lfo_diff);
        v_svf_set_cutoff(f_filter);
        self->output = v_svf_run_2_pole_allpass(f_filter, self->output);
    }

    self->predelay_buffer[(self->predelay_counter)] = self->output;
    ++self->predelay_counter;
    if(unlikely(self->predelay_counter >= self->predelay_size))
    {
        self->predelay_counter = 0;
    }

    self->output = self->predelay_buffer[(self->predelay_counter)];
}

void v_rvb_panic(t_rvb_reverb * self)
{
    register int f_i, f_i2;
    MKFLT * f_tmp;
    int f_count;
    int f_pre_count = self->sr + 5000;
    for(f_i = 0; f_i < f_pre_count; ++f_i)
    {
        self->predelay_buffer[f_i] = 0.0f;
    }

    for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
    {
        f_tmp = self->taps[f_i].tap.input_buffer;
        f_count = self->taps[f_i].tap.buffer_size;
        for(f_i2 = 0; f_i2 < f_count; ++f_i2)
        {
            f_tmp[f_i2] = 0.0f;
        }
    }
}

void g_rvb_reverb_init(t_rvb_reverb * f_result, MKFLT a_sr)
{
    int f_i;

    f_result->color = 1.0f;
    f_result->time = 0.5f;
    f_result->wet = 0.0f;
    f_result->wet_linear = 0.0f;
    f_result->hp_cutoff = -12345.0f;

    f_result->sr = a_sr;

    for(f_i = 0; f_i < PYDAW_REVERB_DIFFUSER_COUNT; ++f_i)
    {
        f_result->diffusers[f_i].pitch = 33.0f + (((MKFLT)f_i) * 7.0f);
    }

    f_result->output = 0.0f;

    g_lfs_init(&f_result->lfo, a_sr);
    v_lfs_sync(&f_result->lfo, 0.0f, 1);

    g_svf_init(&f_result->hp, a_sr);
    v_svf_set_res(&f_result->hp, -36.0f);
    v_svf_set_cutoff_base(&f_result->hp, 60.0f);
    v_svf_set_cutoff(&f_result->hp);

    g_svf_init(&f_result->lp, a_sr);
    v_svf_set_res(&f_result->lp, -36.0f);

    f_result->volume_factor = (1.0f / (MKFLT)PYDAW_REVERB_DIFFUSER_COUNT) * 0.5;

    f_i = 0;

    while(f_i < PYDAW_REVERB_TAP_COUNT)
    {
        g_cmb_init(&f_result->taps[f_i].tap, a_sr, 1);
        ++f_i;
    }

    f_i = 0;

    while(f_i < PYDAW_REVERB_DIFFUSER_COUNT)
    {
        g_svf_init(&f_result->diffusers[f_i].diffuser, a_sr);
        v_svf_set_cutoff_base(&f_result->diffusers[f_i].diffuser,
            f_result->diffusers[f_i].pitch);
        v_svf_set_res(&f_result->diffusers[f_i].diffuser, -6.0f);
        v_svf_set_cutoff(&f_result->diffusers[f_i].diffuser);
        ++f_i;
    }

    f_result->predelay_counter = 0;
    f_result->last_predelay = -1234.0f;
    f_result->predelay_size = (int)(a_sr * 0.01f);

    hpalloc((void**)&f_result->predelay_buffer,
        sizeof(MKFLT) * (a_sr + 5000));

    f_i = 0;
    while(f_i < (a_sr + 5000))
    {
        f_result->predelay_buffer[f_i] = 0.0f;
        ++f_i;
    }

    v_rvb_reverb_set(f_result, 0.5f, 0.0f, 55.5f, 0.01f, 60.0f);
}

#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_REVERB_H */

