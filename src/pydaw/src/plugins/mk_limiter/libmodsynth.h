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

#ifndef MK_LIM_LIBMODSYNTH_H
#define	MK_LIM_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/lib/lmalloc.h"
#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/modules/dynamics/limiter.h"


typedef struct
{
    t_lim_limiter limiter;
}t_mk_lim_mono_modules;

t_mk_lim_mono_modules * v_mk_lim_mono_init(MKFLT, int);

t_mk_lim_mono_modules * v_mk_lim_mono_init(MKFLT a_sr, int a_plugin_uid)
{
    t_mk_lim_mono_modules * f_result;
    hpalloc((void**)&f_result, sizeof(t_mk_lim_mono_modules));
    g_lim_init(&f_result->limiter, a_sr, 1);
    return f_result;
}



#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

