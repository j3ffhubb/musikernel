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

#ifndef WAYV_LIBMODSYNTH_H
#define	WAYV_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

/*Total number of LFOs, ADSRs, other envelopes, etc...
 * Used for the PolyFX mod matrix*/
#define WAYV_MODULATOR_COUNT 8
//How many modular PolyFX
#define WAYV_MODULAR_POLYFX_COUNT 4
#define WAYV_CONTROLS_PER_MOD_EFFECT 3

#define WAYV_FM_MACRO_COUNT 2

#define WAYV_OSC_COUNT 6

#include "../../libmodsynth/constants.h"
#include "../../libmodsynth/lib/osc_core.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/oscillator/osc_simple.h"
#include "../../libmodsynth/modules/oscillator/noise.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/modules/distortion/clipper.h"
#include "../../libmodsynth/modules/modulation/adsr.h"
#include "../../libmodsynth/modules/signal_routing/audio_xfade.h"
#include "../../libmodsynth/modules/modulation/ramp_env.h"
#include "../../libmodsynth/modules/oscillator/lfo_simple.h"
#include "../../libmodsynth/modules/oscillator/osc_wavetable.h"
#include "../../libmodsynth/modules/multifx/multifx3knob.h"
#include "../../libmodsynth/modules/modulation/perc_env.h"

typedef struct
{
    t_wt_wavetables * wavetables;
    t_smoother_linear pitchbend_smoother;
    t_smoother_linear fm_macro_smoother[WAYV_FM_MACRO_COUNT];
    int reset_wavetables;
    t_svf2_filter aa_filter;
}t_wayv_mono_modules;

typedef struct
{
    float fm_osc_values[WAYV_OSC_COUNT];
    float fm_last;

    float osc_linamp;
    int osc_audible;
    int osc_on;
    float osc_uni_spread;
    float osc_fm[WAYV_OSC_COUNT];
    float osc_macro_amp[2];

    t_osc_wav_unison osc_wavtable;

    t_adsr adsr_amp_osc;
    int adsr_amp_on;
}t_wayv_osc;

typedef struct
{
    t_mf3_multi multieffect;
    fp_mf3_run fx_func_ptr;
}t_wayv_pfx_group;

typedef struct
{
    fp_adsr_run adsr_run_func;
    t_adsr adsr_main;
    /*This corresponds to the current sample being processed on this voice.
     * += this to the output buffer when finished.*/
    float current_sample;
    t_ramp_env glide_env;
    t_adsr adsr_amp;
    t_adsr adsr_filter;
    t_ramp_env ramp_env;

    int adsr_lfo_on;
    t_lfs_lfo lfo1;
    float lfo_amount_output, lfo_amp_output, lfo_pitch_output;
    t_adsr adsr_lfo;
    fp_noise_func_ptr noise_func_ptr;

    float note_f;
    int note;

    t_smoother_linear glide_smoother;

    //base pitch for all oscillators, to avoid redundant calculations
    float base_pitch;
    float target_pitch;
    //For simplicity, this is used whether glide is turned on or not
    float last_pitch;

    int perc_env_on;
    t_pnv_perc_env perc_env;

    t_wayv_osc osc[WAYV_OSC_COUNT];

    float noise_amp;
    float noise_linamp;
    t_white_noise white_noise1;
    float noise_sample;
    t_adsr adsr_noise;
    int adsr_noise_on;
    int noise_prefx;

    int adsr_prefx;

    float velocity_track;
    float keyboard_track;

    t_wayv_pfx_group effects[WAYV_MODULAR_POLYFX_COUNT];

    float modulex_current_sample[2];
    float * modulator_outputs[WAYV_MODULATOR_COUNT];

    float amp;
    float master_vol_lin;

    int active_polyfx[WAYV_MODULAR_POLYFX_COUNT];
    int active_polyfx_count;

    //The index of the control to mod, currently 0-2
    int polyfx_mod_ctrl_indexes[WAYV_MODULAR_POLYFX_COUNT]
    [(WAYV_CONTROLS_PER_MOD_EFFECT * WAYV_MODULATOR_COUNT)];

    //How many polyfx_mod_ptrs to iterate through for the current note
    int polyfx_mod_counts[WAYV_MODULAR_POLYFX_COUNT];

    //The index of the modulation source(LFO, ADSR, etc...) to multiply by
    int polyfx_mod_src_index[WAYV_MODULAR_POLYFX_COUNT]
    [(WAYV_CONTROLS_PER_MOD_EFFECT * WAYV_MODULATOR_COUNT)];

    //The value of the mod_matrix knob, multiplied by .01
    float polyfx_mod_matrix_values[WAYV_MODULAR_POLYFX_COUNT]
    [(WAYV_CONTROLS_PER_MOD_EFFECT * WAYV_MODULATOR_COUNT)];

}t_wayv_poly_voice  __attribute__((aligned(16)));

t_wayv_poly_voice * g_wayv_poly_init(float a_sr, t_wayv_mono_modules* a_mono);

/*initialize all of the modules in an instance of poly_voice*/

t_wayv_poly_voice * g_wayv_poly_init(float a_sr, t_wayv_mono_modules* a_mono)
{
    t_wayv_poly_voice * f_voice;
    hpalloc((void**)&f_voice, sizeof(t_wayv_poly_voice));

    int f_i = 0;
    t_wayv_osc * f_osc;

    while(f_i < WAYV_OSC_COUNT)
    {
        f_osc = &f_voice->osc[f_i];
        g_osc_init_osc_wav_unison(&f_osc->osc_wavtable, a_sr);
        f_osc->osc_uni_spread = 0.0f;
        f_osc->osc_on = 0;
        f_osc->fm_last = 0.0;
        g_adsr_init(&f_osc->adsr_amp_osc, a_sr);
        f_osc->adsr_amp_on = 0;
        f_osc->osc_linamp = 1.0f;
        f_osc->osc_audible = 1;

        int f_i2 = 0;
        while(f_i2 < WAYV_OSC_COUNT)
        {
            f_osc->osc_fm[f_i2] = 0.0;
            ++f_i2;
        }
        ++f_i;
    }


    g_adsr_init(&f_voice->adsr_main, a_sr);

    g_white_noise_init(&f_voice->white_noise1, a_sr);
    f_voice->noise_amp = 0;

    g_rmp_init(&f_voice->glide_env, a_sr);

    //f_voice->real_pitch = 60.0f;

    f_voice->target_pitch = 66.0f;
    f_voice->last_pitch = 66.0f;
    f_voice->base_pitch = 66.0f;

    f_voice->current_sample = 0.0f;

    f_voice->amp = 1.0f;
    f_voice->note_f = 1.0f;

    f_voice->noise_linamp = 1.0f;
    f_voice->adsr_prefx = 0;

    f_voice->lfo_amount_output = 0.0f;
    f_voice->lfo_amp_output = 0.0f;
    f_voice->lfo_pitch_output = 0.0f;

    int f_i3 = 0;
    while(f_i3 < WAYV_OSC_COUNT)
    {
        f_osc->fm_osc_values[f_i3] = 0.0f;
        ++f_i3;
    }

    g_adsr_init(&f_voice->adsr_amp, a_sr);
    g_adsr_init(&f_voice->adsr_filter, a_sr);
    g_adsr_init(&f_voice->adsr_noise, a_sr);
    g_adsr_init(&f_voice->adsr_lfo, a_sr);
    f_voice->adsr_noise_on = 0;
    f_voice->adsr_lfo_on = 0;

    f_voice->noise_amp = 0.0f;

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_rmp_init(&f_voice->ramp_env, a_sr);

    g_lfs_init(&f_voice->lfo1, a_sr);

    f_voice->noise_sample = 0.0f;


    for(f_i = 0; f_i < WAYV_MODULAR_POLYFX_COUNT; f_i++)
    {
        g_mf3_init(&f_voice->effects[f_i].multieffect, a_sr, 1);
        f_voice->effects[f_i].fx_func_ptr = v_mf3_run_off;
    }

    f_voice->modulator_outputs[0] = &(f_voice->adsr_amp.output);
    f_voice->modulator_outputs[1] = &(f_voice->adsr_filter.output);
    f_voice->modulator_outputs[2] = &(f_voice->ramp_env.output);
    f_voice->modulator_outputs[3] = &(f_voice->lfo_amount_output);
    f_voice->modulator_outputs[4] = &(f_voice->keyboard_track);
    f_voice->modulator_outputs[5] = &(f_voice->velocity_track);
    f_voice->modulator_outputs[6] = &(a_mono->fm_macro_smoother[0].last_value);
    f_voice->modulator_outputs[7] = &(a_mono->fm_macro_smoother[1].last_value);

    f_voice->noise_func_ptr = f_run_noise_off;

    f_voice->perc_env_on = 0;
    g_pnv_init(&f_voice->perc_env, a_sr);

    return f_voice;
}


void v_wayv_poly_note_off(t_wayv_poly_voice * a_voice, int a_fast);

void v_wayv_poly_note_off(t_wayv_poly_voice * a_voice, int a_fast)
{
    if(a_fast)
    {
        v_adsr_set_fast_release(&a_voice->adsr_main);
    }
    else
    {
        v_adsr_release(&a_voice->adsr_main);
    }

    v_adsr_release(&a_voice->adsr_lfo);
    v_adsr_release(&a_voice->adsr_noise);
    v_adsr_release(&a_voice->adsr_amp);
    v_adsr_release(&a_voice->adsr_filter);

    int f_i = 0;

    while(f_i < WAYV_OSC_COUNT)
    {
        v_adsr_release(&a_voice->osc[f_i].adsr_amp_osc);
        ++f_i;
    }

}

t_wayv_mono_modules * v_wayv_mono_init(float);


/*Initialize any modules that will be run monophonically*/
t_wayv_mono_modules * v_wayv_mono_init(float a_sr)
{
    t_wayv_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_wayv_mono_modules));
    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.2f);

    int f_i = 0;
    while(f_i < WAYV_FM_MACRO_COUNT)
    {
        g_sml_init(&a_mono->fm_macro_smoother[f_i], a_sr, 0.5f, 0.0f, 0.02f);
        ++f_i;
    }

    a_mono->wavetables = g_wt_wavetables_get();
    //indicates that wavetables must be re-pointered immediately
    a_mono->reset_wavetables = 0;
    g_svf2_init(&a_mono->aa_filter, a_sr);
    v_svf2_set_cutoff_base(&a_mono->aa_filter, 120.0f);
    v_svf2_add_cutoff_mod(&a_mono->aa_filter, 0.0f);
    v_svf2_set_res(&a_mono->aa_filter, -6.0f);
    v_svf2_set_cutoff(&a_mono->aa_filter);

    return a_mono;
}


#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

