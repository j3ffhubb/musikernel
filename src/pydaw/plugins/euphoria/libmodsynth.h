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

#ifndef EUPHORIA_LIBMODSYNTH_H
#define	EUPHORIA_LIBMODSYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include <stdio.h>
#include "../../libmodsynth/constants.h"

#include "../../libmodsynth/lib/pitch_core.h"
#include "../../libmodsynth/modules/modulation/adsr.h"
#include "../../libmodsynth/modules/modulation/ramp_env.h"
#include "../../libmodsynth/lib/smoother-linear.h"
#include "../../libmodsynth/modules/oscillator/lfo_simple.h"
#include "../../libmodsynth/modules/oscillator/noise.h"
#include "../../libmodsynth/modules/multifx/multifx3knob.h"
#include "../../libmodsynth/lib/interpolate-sinc.h"
#include "../../libmodsynth/modules/filter/dc_offset_filter.h"

#include "ports.h"

#define EUPHORIA_SINC_INTERPOLATION_POINTS 25
#define EUPHORIA_SINC_INTERPOLATION_POINTS_DIV2 13

#define EUPHORIA_NOISE_COUNT 16

typedef struct
{
    t_mf3_multi multieffect[EUPHORIA_MONO_FX_COUNT];
    fp_mf3_run fx_func_ptr[EUPHORIA_MONO_FX_COUNT];
    t_eq6 eqs;
}t_euphoria_mfx_group;

typedef struct
{
    fp_mf3_run fx_func_ptr;
    fp_mf3_reset fx_reset_ptr;
    t_mf3_multi multieffect;
    int polyfx_mod_counts;
}t_euphoria_pfx_group;

typedef struct
{
    t_smoother_linear pitchbend_smoother;

    t_dco_dc_offset_filter dc_offset_filters[2];
    t_euphoria_mfx_group mfx[EUPHORIA_MONO_FX_GROUPS_COUNT];

    t_white_noise white_noise1[EUPHORIA_NOISE_COUNT];
    int noise_current_index;

    t_sinc_interpolator sinc_interpolator;
}t_euphoria_mono_modules __attribute__((aligned(16)));

typedef struct
{
    int sample_fade_in_end_sample;
    float sample_fade_in_inc;
    int sample_fade_out_start_sample;
    float sample_fade_out_dec;
    float sample_fade_amp;
    t_int_frac_read_head sample_read_heads;
    float vel_sens_output;
}t_euphoria_pfx_sample;

typedef struct
{
    t_adsr adsr_filter;
    fp_adsr_run adsr_run_func;
    t_adsr adsr_amp;
    t_ramp_env glide_env;
    t_ramp_env ramp_env;

    // For glide
    float last_pitch;
    float base_pitch;

    float target_pitch;

    float filter_output;  //For assigning the filter output to

    // This corresponds to the current sample being processed on this voice.
    // += this to the output buffer when finished.
    float current_sample;

    t_lfs_lfo lfo1;

    float note_f;
    float noise_sample;

    t_euphoria_pfx_sample samples[EUPHORIA_MAX_SAMPLE_COUNT];

    t_euphoria_pfx_group effects [EUPHORIA_MODULAR_POLYFX_COUNT];

    float modulex_current_sample[2];

    float * modulator_outputs[EUPHORIA_MODULATOR_COUNT];

    int noise_index;

    float velocity_track;
    float keyboard_track;
    int velocities;

    //Sample indexes for each note to play
    int sample_indexes[EUPHORIA_MAX_SAMPLE_COUNT];
    //The count of sample indexes to iterate through
    int sample_indexes_count;

    //PolyFX modulation streams
     //The index of the control to mod, currently 0-2
    int polyfx_mod_ctrl_indexes[EUPHORIA_MODULAR_POLYFX_COUNT][
        (EUPHORIA_CONTROLS_PER_MOD_EFFECT * EUPHORIA_MODULATOR_COUNT)];
    //The index of the modulation source(LFO, ADSR, etc...) to multiply by
    int polyfx_mod_src_index[EUPHORIA_MODULAR_POLYFX_COUNT][
        (EUPHORIA_CONTROLS_PER_MOD_EFFECT * EUPHORIA_MODULATOR_COUNT)];
    //The value of the mod_matrix knob, multiplied by .01
    float polyfx_mod_matrix_values[EUPHORIA_MODULAR_POLYFX_COUNT][
        (EUPHORIA_CONTROLS_PER_MOD_EFFECT * EUPHORIA_MODULATOR_COUNT)];

    //Active PolyFX to process
    int active_polyfx[EUPHORIA_MODULAR_POLYFX_COUNT];
    int active_polyfx_count;

}t_euphoria_poly_voice __attribute__((aligned(16)));

t_euphoria_poly_voice * g_euphoria_poly_init(float);

/*initialize all of the modules in an instance of poly_voice*/

t_euphoria_poly_voice * g_euphoria_poly_init(float a_sr)
{
    t_euphoria_poly_voice * f_voice;
    hpalloc((void**)&f_voice, sizeof(t_euphoria_poly_voice));

    int f_i = 0;

    g_adsr_init(&f_voice->adsr_amp, a_sr);
    g_adsr_init(&f_voice->adsr_filter, a_sr);

    g_rmp_init(&f_voice->glide_env, a_sr);
    g_rmp_init(&f_voice->ramp_env, a_sr);

    //f_voice->real_pitch = 60.0f;

    f_voice->target_pitch = 66.0f;
    f_voice->last_pitch = 66.0f;
    f_voice->base_pitch = 66.0f;

    f_voice->current_sample = 0.0f;

    f_voice->filter_output = 0.0f;

    g_lfs_init(&f_voice->lfo1, a_sr);

    f_voice->note_f = 1.0f;
    f_voice->noise_sample = 0.0f;

    //From Modulex

    for(f_i = 0; f_i < EUPHORIA_MODULAR_POLYFX_COUNT; ++f_i)
    {
        g_mf3_init(&f_voice->effects[f_i].multieffect, a_sr, 1);
        f_voice->effects[f_i].fx_func_ptr = v_mf3_run_off;
    }

    f_voice->modulator_outputs[0] = &(f_voice->adsr_amp.output);
    f_voice->modulator_outputs[1] = &(f_voice->adsr_filter.output);
    f_voice->modulator_outputs[2] = &(f_voice->ramp_env.output);
    f_voice->modulator_outputs[3] = &(f_voice->lfo1.output);
    f_voice->modulator_outputs[4] = &(f_voice->keyboard_track);
    f_voice->modulator_outputs[5] = &(f_voice->velocity_track);

    f_voice->noise_index = 0;
    f_voice->velocities = 0;
    f_voice->sample_indexes_count = 0;

    for(f_i = 0; f_i < EUPHORIA_MAX_SAMPLE_COUNT; ++f_i)
    {
        g_ifh_init(&f_voice->samples[f_i].sample_read_heads);
        f_voice->samples[f_i].vel_sens_output = 0.0f;
        f_voice->sample_indexes[f_i] = 0;
    }

    return f_voice;
}


void v_euphoria_poly_note_off(t_euphoria_poly_voice * a_voice,
        int a_fast_release);

void v_euphoria_poly_note_off(t_euphoria_poly_voice * a_voice,
        int a_fast_release)
{
    if(a_fast_release)
    {
        v_adsr_set_fast_release(&a_voice->adsr_amp);
    }
    else
    {
        v_adsr_release(&a_voice->adsr_amp);
    }

    v_adsr_release(&a_voice->adsr_filter);
}

t_euphoria_mono_modules * g_euphoria_mono_init(float a_sr);

t_euphoria_mono_modules * g_euphoria_mono_init(float a_sr)
{
    t_euphoria_mono_modules * a_mono;
    hpalloc((void**)&a_mono, sizeof(t_euphoria_mono_modules));

    g_sml_init(&a_mono->pitchbend_smoother, a_sr, 1.0f, -1.0f, 0.1f);
    g_sinc_init(&a_mono->sinc_interpolator,
        EUPHORIA_SINC_INTERPOLATION_POINTS, 6000, 8000.0f, a_sr, 0.42f);
    a_mono->noise_current_index = 0;

    int f_i;

    for(f_i = 0; f_i < 2; ++f_i)
    {
        g_dco_init(&a_mono->dc_offset_filters[f_i], a_sr);
    }

    int f_i2;

    for(f_i = 0; f_i < EUPHORIA_MONO_FX_GROUPS_COUNT; ++f_i)
    {
        g_eq6_init(&a_mono->mfx[f_i].eqs, a_sr);

        for(f_i2 = 0; f_i2 < EUPHORIA_MONO_FX_COUNT; ++f_i2)
        {
            g_mf3_init(&a_mono->mfx[f_i].multieffect[f_i2], a_sr, 1);
            a_mono->mfx[f_i].fx_func_ptr[f_i2] = v_mf3_run_off;
        }
    }

    for(f_i = 0; f_i < EUPHORIA_NOISE_COUNT; ++f_i)
    {
        g_white_noise_init(&a_mono->white_noise1[f_i], a_sr);
    }

    return a_mono;
}


#ifdef	__cplusplus
}
#endif

#endif	/* LIBMODSYNTH_H */

