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

#ifndef TRIGGERFX_LIBMODSYNTH_H
#define	TRIGGERFX_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/osc_core.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/modulation/env_follower.h"
#include "../../libmodsynth/modules/modulation/gate.h"
#include "../../libmodsynth/modules/distortion/glitch_v2.h"


typedef struct
{
    t_smoother_linear pitchbend_smoother;

    MKFLT current_sample0;
    MKFLT current_sample1;

    MKFLT vol_linear;

    t_smoother_linear gate_wet_smoother;
    t_smoother_linear glitch_time_smoother;

    t_gat_gate gate;
    MKFLT gate_on;

    t_glc_glitch_v2 glitch;
    MKFLT glitch_on;
}t_triggerfx_mono_modules;

t_triggerfx_mono_modules * v_triggerfx_mono_init(MKFLT, int);

t_triggerfx_mono_modules * v_triggerfx_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_triggerfx_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_triggerfx_mono_modules));

    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.1f);

    g_sml_init(&a_mono->gate_wet_smoother,a_sr, 100.0f, 0.0f, 0.01f);
    a_mono->gate_wet_smoother.last_value = 0.0f;

    a_mono->vol_linear = 1.0f;

    g_gat_init(&a_mono->gate, a_sr);
    a_mono->gate_on = 0.0f;

    g_glc_glitch_v2_init(&a_mono->glitch, a_sr);
    a_mono->glitch_on = 0.0f;
    g_sml_init(&a_mono->glitch_time_smoother, a_sr, 0.10f, 0.01f, 0.01f);

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

