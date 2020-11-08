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

#ifndef MK_VOCODER_LIBMODSYNTH_H
#define	MK_VOCODER_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/filter/vocoder.h"

typedef struct
{
    t_smoother_linear carrier_smoother;
    t_smoother_linear wet_smoother;
    t_vdr_vocoder vocoder;
    t_smoother_linear modulator_smoother;
}t_mk_vocoder_mono_modules;

t_mk_vocoder_mono_modules * v_mk_vocoder_mono_init(MKFLT, int);

t_mk_vocoder_mono_modules * v_mk_vocoder_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_mk_vocoder_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_mk_vocoder_mono_modules));
    g_sml_init(&a_mono->wet_smoother, a_sr, 0.0f, -500.0f, 0.1f);
    g_vdr_init(&a_mono->vocoder, a_sr);
    g_sml_init(&a_mono->carrier_smoother, a_sr, 0.0f, -500.0f, 0.1f);
    g_sml_init(&a_mono->modulator_smoother, a_sr, 0.0f, -500.0f, 0.1f);

    return a_mono;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

