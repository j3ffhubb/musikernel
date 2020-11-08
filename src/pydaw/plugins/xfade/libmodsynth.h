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

#ifndef XFADE_LIBMODSYNTH_H
#define	XFADE_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/modulation/env_follower.h"
#include "../../libmodsynth/modules/signal_routing/panner2.h"

typedef struct
{
    MKFLT current_sample0;
    MKFLT current_sample1;

    t_smoother_linear pan_smoother;

    t_pn2_panner2 panner;
}t_xfade_mono_modules;

t_xfade_mono_modules * v_xfade_mono_init(MKFLT, int);

t_xfade_mono_modules * v_xfade_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_xfade_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_xfade_mono_modules));

    g_sml_init(&a_mono->pan_smoother, a_sr, 100.0f, -100.0f, 0.1f);
    a_mono->pan_smoother.last_value = 0.0f;

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

