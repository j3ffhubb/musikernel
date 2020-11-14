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

#ifndef VOCODER_H
#define	VOCODER_H

#include "svf_stereo.h"
#include "../modulation/env_follower2.h"

#define VOCODER_BAND_COUNT 64
#define VOCODER_BAND_COUNT_M1 (VOCODER_BAND_COUNT - 1)

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    t_state_variable_filter m_filter;
    t_enf2_env_follower env_follower;
    t_svf2_filter c_filter;
}t_vdr_band;

typedef struct
{
    MKFLT output0, output1;
    t_vdr_band bands[VOCODER_BAND_COUNT];
    t_vdr_band low_band;
    t_vdr_band high_band;
}t_vdr_vocoder;

#ifdef	__cplusplus
}
#endif

void g_vdr_band_init(t_vdr_band * self, MKFLT a_sr, MKFLT a_pitch, MKFLT a_res)
{
    MKFLT f_release = (1.0f / f_pit_midi_note_to_hz(a_pitch)) * 100.0f;
    g_svf_init(&self->m_filter, a_sr);
    v_svf_set_res(&self->m_filter, a_res);
    v_svf_set_cutoff_base(&self->m_filter, a_pitch);
    v_svf_set_cutoff(&self->m_filter);
    g_enf_init(&self->env_follower, a_sr);
    v_enf_set(&self->env_follower, 0.001f, f_release);
    g_svf2_init(&self->c_filter, a_sr);
    v_svf2_set_res(&self->c_filter, a_res);
    v_svf2_set_cutoff_base(&self->c_filter, a_pitch);
    v_svf2_set_cutoff(&self->c_filter);
}

void g_vdr_init(t_vdr_vocoder * self, MKFLT a_sr)
{
    self->output0 = 0.0f;
    self->output1 = 0.0f;

    int f_i;
    MKFLT f_freq = f_pit_hz_to_midi_note(240.0f);
    MKFLT f_inc = (f_pit_hz_to_midi_note(7200.0f) - f_freq) /
        (MKFLT)VOCODER_BAND_COUNT;

    for(f_i = 0; f_i < VOCODER_BAND_COUNT; ++f_i)
    {
        g_vdr_band_init(&self->bands[f_i], a_sr, f_freq, -0.01f);
        f_freq += f_inc;
    }

    g_vdr_band_init(&self->low_band, a_sr,
        f_pit_hz_to_midi_note(200.0f), -15.0f);
    g_vdr_band_init(&self->high_band, a_sr,
        f_pit_hz_to_midi_note(6000.0f), -18.0f);

}

void v_vdr_run(t_vdr_vocoder * self, MKFLT a_mod_in0, MKFLT a_mod_in1,
        MKFLT a_input0, MKFLT a_input1)
{
    int f_i;
    MKFLT f_env_val;
    t_state_variable_filter * f_m_filter;
    t_svf2_filter * f_c_filter;
    t_enf2_env_follower * f_envf;
    MKFLT f_mono_input = (a_mod_in0 + a_mod_in1) * 0.5f;

    self->output0 = 0.0f;
    self->output1 = 0.0f;

    for(f_i = 0; f_i < VOCODER_BAND_COUNT; ++f_i)
    {
        f_m_filter = &self->bands[f_i].m_filter;
        f_envf = &self->bands[f_i].env_follower;
        f_c_filter = &self->bands[f_i].c_filter;

        f_env_val =
            v_svf_run_2_pole_bp(f_m_filter, f_mono_input);
        v_enf_run(f_envf, f_env_val);

        v_svf2_run_2_pole_bp(f_c_filter, a_input0, a_input1);
        self->output0 += f_c_filter->output0 * f_envf->envelope;
        self->output1 += f_c_filter->output1 * f_envf->envelope;
    }

    f_m_filter = &self->low_band.m_filter;
    f_envf = &self->low_band.env_follower;
    f_c_filter = &self->low_band.c_filter;

    f_env_val =
        v_svf_run_2_pole_lp(f_m_filter, f_mono_input);
    v_enf_run(f_envf, f_env_val);

    v_svf2_run_2_pole_lp(f_c_filter, a_input0, a_input1);
    self->output0 += f_c_filter->output0 * f_envf->envelope;
    self->output1 += f_c_filter->output1 * f_envf->envelope;

    f_env_val *= 0.25f;
    self->output0 += f_env_val;
    self->output1 += f_env_val;

    f_m_filter = &self->high_band.m_filter;
    f_envf = &self->high_band.env_follower;
    f_c_filter = &self->high_band.c_filter;

    f_env_val =
        v_svf_run_2_pole_hp(f_m_filter, f_mono_input);
    v_enf_run(f_envf, f_env_val);

    v_svf2_run_2_pole_hp(f_c_filter, a_input0, a_input1);
    self->output0 += f_c_filter->output0 * f_envf->envelope;
    self->output1 += f_c_filter->output1 * f_envf->envelope;

    f_env_val *= 0.25f;
    self->output0 += f_env_val;
    self->output1 += f_env_val;
}


#endif	/* VOCODER_H */

