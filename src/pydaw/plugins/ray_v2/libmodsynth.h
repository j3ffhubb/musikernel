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

#ifndef RAYV2_LIBMODSYNTH_H
#define	RAYV2_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/osc_core.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/oscillator/osc_simple.h"
#include "../../libmodsynth/modules/oscillator/noise.h"
#include "../../libmodsynth/modules/filter/nosvf.h"
#include "../../libmodsynth/modules/distortion/multi.h"
#include "../../libmodsynth/modules/modulation/adsr.h"
#include "../../libmodsynth/modules/signal_routing/audio_xfade.h"
#include "../../libmodsynth/modules/modulation/ramp_env.h"
#include "../../libmodsynth/modules/oscillator/lfo_simple.h"

typedef struct
{
    t_smoother_linear filter_smoother;
    t_smoother_linear pitchbend_smoother;
    t_smoother_linear lfo_smoother;
    t_nosvf_filter aa_filter;
}t_rayv2_mono_modules;


typedef struct
{
    float   amp;
    float note_f;
    int note;
    float osc1_linamp;
    float osc2_linamp;
    float noise_linamp;
    int hard_sync;
    int noise_prefx;
    fp_noise_func_ptr noise_func_ptr;
    int adsr_prefx;
    float unison_spread1;
    float unison_spread2;
    float dist_out_gain;
    float osc1pb;
    float osc2pb;

    float lfo_amp_output, lfo_pitch_output, lfo_filter_output;

    t_smoother_linear glide_smoother;
    t_ramp_env glide_env;
    t_lfs_lfo lfo1;
    t_ramp_env pitch_env;
    //For glide
    float last_pitch;
      //base pitch for all oscillators, to avoid redundant calculations
    float base_pitch;
    float target_pitch;

    float osc1_pitch_adjust, osc2_pitch_adjust;

    t_osc_simple_unison osc_unison1;
    t_osc_simple_unison osc_unison2;
    t_white_noise white_noise1;

    float noise_amp;
    float filter_keytrk;

    t_adsr adsr_filter;
    fp_adsr_run adsr_run_func;
    t_adsr adsr_amp;
    t_nosvf_filter svf_filter;
    fp_nosvf_run_filter svf_function;

    t_mds_multidist mdist;
    fp_multi_dist mdist_fp;
}t_rayv2_poly_voice  __attribute__((aligned(16)));

t_rayv2_poly_voice * g_rayv2_poly_init(float);



t_rayv2_poly_voice * g_rayv2_poly_init(float a_sr)
{
    t_rayv2_poly_voice * f_voice;
    hpalloc((void**)&f_voice, sizeof(t_rayv2_poly_voice));

    g_osc_simple_unison_init(&f_voice->osc_unison1, a_sr);
    g_osc_simple_unison_init(&f_voice->osc_unison2, a_sr);

    f_voice->osc1_pitch_adjust = 0.0f;
    f_voice->osc2_pitch_adjust = 0.0f;

    g_nosvf_init(&f_voice->svf_filter, a_sr);
    g_mds_init(&f_voice->mdist);
    f_voice->mdist_fp = g_mds_get_fp(0);

    f_voice->filter_keytrk = 0.0f;

    g_adsr_init(&f_voice->adsr_amp, a_sr);
    g_adsr_init(&f_voice->adsr_filter, a_sr);

    g_white_noise_init(&f_voice->white_noise1, a_sr);
    f_voice->noise_amp = 0;
    f_voice->noise_func_ptr = f_run_noise_off;

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_rmp_init(&f_voice->pitch_env, a_sr);

    //f_voice->real_pitch = 60.0f;

    f_voice->target_pitch = 66.0f;
    f_voice->last_pitch = 66.0f;
    f_voice->base_pitch = 66.0f;

    g_lfs_init(&f_voice->lfo1, a_sr);

    f_voice->lfo_amp_output = 0.0f;
    f_voice->lfo_filter_output = 0.0f;
    f_voice->lfo_pitch_output = 0.0f;

    f_voice->amp = 1.0f;
    f_voice->note_f = 1.0f;
    f_voice->osc1_linamp = 1.0f;
    f_voice->osc2_linamp = 1.0f;
    f_voice->noise_linamp = 1.0f;

    f_voice->hard_sync = 0;
    f_voice->adsr_prefx = 0;
    f_voice->unison_spread1 = 0.5f;
    f_voice->unison_spread2 = 0.5f;

    return f_voice;
}


void v_rayv2_poly_note_off(t_rayv2_poly_voice * a_voice, int a_fast);

void v_rayv2_poly_note_off(t_rayv2_poly_voice * a_voice, int a_fast)
{
    if(a_fast)
    {
        v_adsr_set_fast_release(&a_voice->adsr_amp);
    }
    else
    {
        v_adsr_release(&a_voice->adsr_amp);
    }

    v_adsr_release(&a_voice->adsr_filter);
}

t_rayv2_mono_modules * v_rayv2_mono_init(float);


/*Initialize any modules that will be run monophonically*/
t_rayv2_mono_modules * v_rayv2_mono_init(float a_sr)
{
    t_rayv2_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_rayv2_mono_modules));
    g_sml_init(&a_mono->filter_smoother, a_sr, 124.0f, 20.0f, 0.2f);
    g_sml_init(&a_mono->lfo_smoother, a_sr, 1600.0f, 10.0f, 0.2f);
    //To prevent low volume and brightness at the first note-on(s)
    a_mono->filter_smoother.last_value = 100.0f;
    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.1f);
    g_nosvf_init(&a_mono->aa_filter, a_sr);

    v_nosvf_set_cutoff_base(&a_mono->aa_filter, 120.0f);
    v_nosvf_add_cutoff_mod(&a_mono->aa_filter, 0.0f);
    v_nosvf_set_res(&a_mono->aa_filter, -6.0f);
    v_nosvf_set_cutoff(&a_mono->aa_filter);

    return a_mono;
}


#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */
