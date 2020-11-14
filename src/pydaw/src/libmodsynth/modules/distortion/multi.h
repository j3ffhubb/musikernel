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

#ifndef MULTI_DIST_H
#define	MULTI_DIST_H

#include "clipper.h"
#include "foldback.h"
#include "../signal_routing/audio_xfade.h"


#ifdef	__cplusplus
extern "C" {
#endif

typedef struct{
    MKFLT gain, in_db;
    t_clipper clipper1;
    t_audio_xfade dist_dry_wet;
}t_mds_multidist;

#ifdef	__cplusplus
}
#endif

typedef MKFLT (*fp_multi_dist)(t_mds_multidist*, MKFLT, MKFLT);

MKFLT f_multi_dist_off(t_mds_multidist* self, MKFLT a_sample, MKFLT a_out)
{
    return a_sample;
}

MKFLT f_multi_dist_clip(t_mds_multidist* self, MKFLT a_sample, MKFLT a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_clp_clip(&self->clipper1, a_sample * self->gain) * a_out);
}

MKFLT f_multi_dist_foldback(t_mds_multidist* self, MKFLT a_sample, MKFLT a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_fbk_mono(a_sample * self->gain) * a_out);
}

__thread fp_multi_dist MULTI_DIST_FP[]
__attribute__((aligned(CACHE_LINE_SIZE))) = {
    f_multi_dist_off, f_multi_dist_clip, f_multi_dist_foldback
};

fp_multi_dist g_mds_get_fp(int index)
{
    assert(index >= 0 && index <= 2);
    return MULTI_DIST_FP[index];
}

void v_mds_set_gain(t_mds_multidist * self, MKFLT a_db)
{
    if((self->in_db) != a_db)
    {
        self->in_db = a_db;
        self->gain = f_db_to_linear(a_db);
    }
}

void g_mds_init(t_mds_multidist * self)
{
    self->gain = 1.0f;
    self->in_db = -12345.068f;
    g_clp_init(&self->clipper1);
    g_axf_init(&self->dist_dry_wet, -3.0f);
}

#endif	/* MULTI_DIST_H */

