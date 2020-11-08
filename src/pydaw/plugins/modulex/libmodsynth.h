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

#ifndef MODULEX_LIBMODSYNTH_H
#define	MODULEX_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/modules/multifx/multifx3knob.h"
#include "../../libmodsynth/lib/osc_core.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/lib/spectrum_analyzer.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/delay/lms_delay.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/modulation/env_follower.h"
#include "../../libmodsynth/modules/delay/reverb.h"
#include "../../libmodsynth/modules/filter/peak_eq.h"
#include "../../libmodsynth/modules/modulation/gate.h"
#include "../../libmodsynth/modules/distortion/glitch_v2.h"


typedef struct
{
    t_mf3_multi multieffect[8];
    fp_mf3_run fx_func_ptr[8];

    t_smoother_linear time_smoother;

    MKFLT current_sample0;
    MKFLT current_sample1;

    MKFLT vol_linear;
    t_smoother_linear smoothers[8][3];
}t_modulex_mono_modules;

t_modulex_mono_modules * v_modulex_mono_init(MKFLT, int);

t_modulex_mono_modules * v_modulex_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_modulex_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_modulex_mono_modules));

    int f_i = 0;

    while(f_i < 8)
    {
        g_mf3_init(&a_mono->multieffect[f_i], a_sr, 1);
        a_mono->fx_func_ptr[f_i] = v_mf3_run_off;
        int f_i2 = 0;
        while(f_i2 < 3)
        {
            g_sml_init(&a_mono->smoothers[f_i][f_i2],
                a_sr, 127.0f, 0.0f, 0.1f);
            ++f_i2;
        }
        ++f_i;
    }

    g_sml_init(&a_mono->time_smoother, a_sr, 100.0f, 10.0f, 0.1f);

    a_mono->vol_linear = 1.0f;

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

