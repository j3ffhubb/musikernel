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

#ifndef SIMPLE_FADER_LIBMODSYNTH_H
#define	SIMPLE_FADER_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/modulation/env_follower.h"

typedef struct
{
    MKFLT current_sample0;
    MKFLT current_sample1;

    MKFLT vol_linear;

    t_smoother_linear * volume_smoother;
}t_sfader_mono_modules;

t_sfader_mono_modules * v_sfader_mono_init(MKFLT, int);

t_sfader_mono_modules * v_sfader_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_sfader_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_sfader_mono_modules));

    a_mono->volume_smoother =
            g_sml_get_smoother_linear(a_sr, 0.0f, -50.0f, 0.1f);
    a_mono->volume_smoother->last_value = 0.0f;

    a_mono->vol_linear = 1.0f;

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

