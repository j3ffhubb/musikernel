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

#ifndef MKEQ_LIBMODSYNTH_H
#define	MKEQ_LIBMODSYNTH_H

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
#include "../../libmodsynth/modules/delay/reverb.h"
#include "../../libmodsynth/modules/filter/peak_eq.h"
#include "../../libmodsynth/modules/modulation/gate.h"
#include "../../libmodsynth/modules/distortion/glitch_v2.h"

#define MKEQ_EQ_COUNT 6

typedef struct
{
    MKFLT current_sample0;
    MKFLT current_sample1;

    MKFLT vol_linear;

    t_pkq_peak_eq eqs[MKEQ_EQ_COUNT];
    t_spa_spectrum_analyzer * spectrum_analyzer;
}t_mkeq_mono_modules;

t_mkeq_mono_modules * v_mkeq_mono_init(MKFLT, int);

t_mkeq_mono_modules * v_mkeq_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_mkeq_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_mkeq_mono_modules));

    int f_i = 0;

    while(f_i < MKEQ_EQ_COUNT)
    {
        g_pkq_init(&a_mono->eqs[f_i], a_sr);
        ++f_i;
    }

    a_mono->vol_linear = 1.0f;

    a_mono->spectrum_analyzer =
        g_spa_spectrum_analyzer_get(4096, a_plugin_uid);

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

