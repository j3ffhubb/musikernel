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

#ifndef MKDELAY_LIBMODSYNTH_H
#define	MKDELAY_LIBMODSYNTH_H

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

#define MODULEX_EQ_COUNT 6

typedef struct
{
    t_lms_delay * delay;
    t_smoother_linear * time_smoother;

    MKFLT current_sample0;
    MKFLT current_sample1;

    MKFLT vol_linear;

}t_mkdelay_mono_modules;

t_mkdelay_mono_modules * v_mkdelay_mono_init(MKFLT, int);

t_mkdelay_mono_modules * v_mkdelay_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_mkdelay_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_mkdelay_mono_modules));

    a_mono->delay = g_ldl_get_delay(1, a_sr);
    a_mono->time_smoother =
            g_sml_get_smoother_linear(a_sr, 100.0f, 10.0f, 0.1f);

    a_mono->vol_linear = 1.0f;

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

