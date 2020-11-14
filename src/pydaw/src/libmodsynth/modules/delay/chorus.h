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

#ifndef CHORUS_H
#define	CHORUS_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/interpolate-cubic.h"
#include "../../lib/amp.h"
#include "../../lib/lmalloc.h"
#include "../oscillator/lfo_simple.h"
#include "../filter/svf_stereo.h"

typedef struct
{
    MKFLT * buffer;
    MKFLT wet_lin, wet_db, freq_last, mod_amt;
    MKFLT output0, output1;
    MKFLT delay_offset_amt, delay_offset;
    MKFLT pos_left, pos_right;
    int buffer_size, buffer_ptr;
    MKFLT buffer_size_MKFLT;
    t_lfs_lfo lfo;
    t_svf2_filter hp;
    t_svf2_filter lp;
}t_crs_chorus;

void v_crs_free(t_crs_chorus *);
void v_crs_chorus_set(t_crs_chorus*, MKFLT, MKFLT);
void v_crs_chorus_run(t_crs_chorus*, MKFLT, MKFLT);

void g_crs_init(t_crs_chorus * f_result, MKFLT a_sr, int a_huge_pages)
{
    f_result->buffer_size = (int)(a_sr * 0.050f);
    f_result->buffer_size_MKFLT = ((MKFLT)(f_result->buffer_size));

    if(a_huge_pages)
    {
        hpalloc((void**)&f_result->buffer,
            sizeof(MKFLT) * f_result->buffer_size);
    }
    else
    {
        lmalloc((void**)&f_result->buffer,
            sizeof(MKFLT) * f_result->buffer_size);
    }

    int f_i = 0;
    while(f_i < f_result->buffer_size)
    {
        f_result->buffer[f_i] = 0.0f;
        f_i++;
    }

    f_result->pos_left = 0.0f;
    f_result->pos_right = 0.0f;
    f_result->buffer_ptr = 0;
    f_result->delay_offset_amt =  a_sr * 0.03f;
    f_result->delay_offset = 0.0f;
    g_lfs_init(&f_result->lfo, a_sr);
    f_result->wet_lin = 0.0f;
    f_result->wet_db = -99.99f;
    f_result->mod_amt = a_sr * 0.01f;
    f_result->freq_last = -99.99f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    g_svf2_init(&f_result->lp, a_sr);
    g_svf2_init(&f_result->hp, a_sr);
    v_svf2_set_res(&f_result->lp, -15.0f);
    v_svf2_set_res(&f_result->hp, -15.0f);
    v_svf2_set_cutoff_base(&f_result->hp, 50.0f);
    v_svf2_set_cutoff(&f_result->hp);
    v_svf2_set_cutoff_base(&f_result->lp, 90.0f);
    v_svf2_set_cutoff(&f_result->lp);
    v_lfs_sync(&f_result->lfo, 0.0f, 1);
}

void v_crs_chorus_set(t_crs_chorus* a_crs, MKFLT a_freq, MKFLT a_wet)
{
    if(a_wet != (a_crs->wet_db))
    {
        a_crs->wet_db = a_wet;
        a_crs->wet_lin = f_db_to_linear_fast(a_wet);
    }

    if(a_freq != (a_crs->freq_last))
    {
        a_crs->freq_last = a_freq;
        v_lfs_set(&a_crs->lfo, a_freq);
    }
}

void v_crs_chorus_run(t_crs_chorus* a_crs, MKFLT a_input0, MKFLT a_input1)
{
    a_crs->buffer[(a_crs->buffer_ptr)] = (a_input0 + a_input1) * 0.5f;

    a_crs->delay_offset = ((MKFLT)(a_crs->buffer_ptr)) -
            (a_crs->delay_offset_amt);

    v_lfs_run(&a_crs->lfo);

    a_crs->pos_left = ((a_crs->delay_offset) + ((a_crs->lfo.output) *
            (a_crs->mod_amt)));

    if((a_crs->pos_left) >= (a_crs->buffer_size_MKFLT))
    {
        a_crs->pos_left -= (a_crs->buffer_size_MKFLT);
    }
    else if((a_crs->pos_left) < 0.0f)
    {
        a_crs->pos_left += (a_crs->buffer_size_MKFLT);
    }

    a_crs->pos_right = ((a_crs->delay_offset) + ((a_crs->lfo.output) *
            (a_crs->mod_amt) * -1.0f));

    if((a_crs->pos_right) >= (a_crs->buffer_size_MKFLT))
    {
        a_crs->pos_right -= (a_crs->buffer_size_MKFLT);
    }
    else if((a_crs->pos_right) < 0.0f)
    {
        a_crs->pos_right += (a_crs->buffer_size_MKFLT);
    }

    a_crs->output0 = a_input0 + (f_cubic_interpolate_ptr_wrap(a_crs->buffer,
            (a_crs->buffer_size), (a_crs->pos_left)) * (a_crs->wet_lin));
    a_crs->output1 = a_input1 +  (f_cubic_interpolate_ptr_wrap(a_crs->buffer,
            (a_crs->buffer_size), (a_crs->pos_right)) * (a_crs->wet_lin));

    v_svf2_run_2_pole_hp(&a_crs->hp, a_crs->output0, a_crs->output1);
    v_svf2_run_2_pole_lp(&a_crs->lp, a_crs->hp.output0, a_crs->hp.output1);

    a_crs->output0 = a_crs->lp.output0;
    a_crs->output1 = a_crs->lp.output1;

    ++a_crs->buffer_ptr;
    if((a_crs->buffer_ptr) >= (a_crs->buffer_size))
    {
        a_crs->buffer_ptr = 0;
    }
}

void v_crs_free(t_crs_chorus * a_crs)
{
    free(a_crs->buffer);
    //free(a_crs);
}

#ifdef	__cplusplus
}
#endif

#endif	/* CHORUS_H */

