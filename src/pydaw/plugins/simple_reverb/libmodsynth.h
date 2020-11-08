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

#ifndef SREVERB_LIBMODSYNTH_H
#define	SREVERB_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/modulation/env_follower.h"
#include "../../libmodsynth/modules/delay/reverb.h"


typedef struct
{
    t_smoother_linear reverb_smoother;
    t_smoother_linear reverb_dry_smoother;
    t_rvb_reverb reverb;
}t_sreverb_mono_modules;

t_sreverb_mono_modules * v_sreverb_mono_init(MKFLT, int);

t_sreverb_mono_modules * v_sreverb_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_sreverb_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_sreverb_mono_modules));

    g_sml_init(&a_mono->reverb_smoother, a_sr, 100.0f, 0.0f, 0.001f);
    a_mono->reverb_smoother.last_value = 0.0f;
    g_sml_init(&a_mono->reverb_dry_smoother, a_sr, 100.0f, 0.0f, 0.001f);
    a_mono->reverb_dry_smoother.last_value = 1.0f;

    g_rvb_reverb_init(&a_mono->reverb, a_sr);

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

