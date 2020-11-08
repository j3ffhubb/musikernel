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

#ifndef SIDECHAIN_COMP_H
#define	SIDECHAIN_COMP_H

#include "../../lib/amp.h"
#include "../../lib/lms_math.h"
#include "../modulation/env_follower2.h"
#include "../signal_routing/audio_xfade.h"
#include "../../lib/peak_meter.h"
#include "../filter/svf.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT pitch, ratio, thresh, wet, attack, release;
    t_state_variable_filter filter;
    MKFLT output0, output1;
    t_enf2_env_follower env_follower;
    t_audio_xfade xfade;
    t_pkm_redux peak_tracker;
}t_scc_sidechain_comp;

#ifdef	__cplusplus
}
#endif


void g_scc_init(t_scc_sidechain_comp * self, MKFLT a_sr)
{
    g_enf_init(&self->env_follower, a_sr);
    g_axf_init(&self->xfade, -3.0f);
    self->attack = 999.99f;
    self->release = 999.99f;
    self->pitch = 999.99f;
    self->ratio = 999.99f;
    self->thresh = 999.99f;
    self->wet = 999.99f;
    g_svf_init(&self->filter, a_sr);
    v_svf_set_cutoff_base(&self->filter, 66.0f);
    v_svf_set_res(&self->filter, -24.0f);
    v_svf_set_cutoff(&self->filter);
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    g_pkm_redux_init(&self->peak_tracker, a_sr);
}

void v_scc_set(t_scc_sidechain_comp *self, MKFLT a_thresh, MKFLT a_ratio,
    MKFLT a_attack, MKFLT a_release, MKFLT a_wet)
{
    self->thresh = a_thresh;
    self->ratio = a_ratio;

    if(self->attack != a_attack || self->release != a_release)
    {
        self->attack = a_attack;
        self->release = a_release;
        v_enf_set(&self->env_follower, a_attack, a_release);
    }

    if(self->wet != a_wet)
    {
        self->wet = a_wet;
        v_axf_set_xfade(&self->xfade, a_wet);
    }
}

void v_scc_run_comp(t_scc_sidechain_comp *self,
    MKFLT a_input0, MKFLT a_input1, MKFLT a_output0, MKFLT a_output1)
{
    MKFLT f_gain;

    v_enf_run(&self->env_follower,
        f_lms_max(f_lms_abs(a_input0), f_lms_abs(a_input1)));

    f_gain = self->thresh - f_linear_to_db_fast(self->env_follower.envelope);

    if(f_gain < 0.0f)
    {
        f_gain *= self->ratio;
        f_gain = f_db_to_linear_fast(f_gain);
        f_gain = v_svf_run_4_pole_lp(&self->filter, f_gain);

        self->output0 = f_axf_run_xfade(
            &self->xfade, a_output0, a_output0 * f_gain);
        self->output1 = f_axf_run_xfade(
            &self->xfade, a_output1, a_output1 * f_gain);
        v_pkm_redux_run(&self->peak_tracker, f_gain);
    }
    else
    {
        self->output0 = a_output0;
        self->output1 = a_output1;
        v_pkm_redux_run(&self->peak_tracker, 1.0f);
    }
}

#endif	/* SIDECHAIN_COMP_H */

