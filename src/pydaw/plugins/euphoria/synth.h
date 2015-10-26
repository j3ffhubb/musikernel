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

#ifndef EUPHORIA_SYNTH_H
#define EUPHORIA_SYNTH_H

#include "../../include/pydaw_plugin.h"
#include "ports.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/lib/voice.h"
#include "../../libmodsynth/lib/pitch_core.h"
#include "libmodsynth.h"
#include "../../libmodsynth/lib/interpolate-linear.h"
#include "../../libmodsynth/lib/interpolate-cubic.h"

#define EUPHORIA_POLYPHONY 20
#define EUPHORIA_POLYPHONY_THRESH 16

// How many buffers in between slow indexing operations.
// Buffer == users soundcard latency settings, ie: 512 samples
#define EUPHORIA_SLOW_INDEX_COUNT 64

struct st_euphoria;

typedef struct
{
    PYFX_Data *basePitch;
    PYFX_Data *low_note;
    PYFX_Data *high_note;
    PYFX_Data *sample_vol;
    PYFX_Data *sampleStarts;
    PYFX_Data *sampleEnds;
    PYFX_Data *sampleLoopStarts;
    PYFX_Data *sampleLoopEnds;
    PYFX_Data *sampleLoopModes;
    PYFX_Data *sampleFadeInEnds;
    PYFX_Data *sampleFadeOutStarts;
    PYFX_Data *sample_vel_sens;
    PYFX_Data *sample_vel_low;
    PYFX_Data *sample_vel_high;
    PYFX_Data *sample_pitch;
    PYFX_Data *sample_tune;
    PYFX_Data *sample_interpolation_mode;
    PYFX_Data *noise_amp;
    PYFX_Data *noise_type;
    //For the per-sample interpolation modes
    int (*ratio_function_ptr)(struct st_euphoria * plugin_data, int n);
    void (*interpolation_mode)(struct st_euphoria * plugin_data, int n, int ch);
    float       sample_last_interpolated_value;
    t_wav_pool_item * wavpool_items;
    float       sampleStartPos;
    float       sampleEndPos;
    // There is no sampleLoopEndPos because the regular
    // sample end is re-used for this purpose
    float       sampleLoopStartPos;
    float       sample_amp;     //linear, for multiplying
    float adjusted_base_pitch;
    fp_noise_func_ptr noise_func_ptr;
    int noise_index;
    float noise_linamp;
}t_euphoria_sample;

typedef struct st_euphoria
{
    PYFX_Data *output[2];
    t_euphoria_sample samples[EUPHORIA_MAX_SAMPLE_COUNT];

    PYFX_Data *mfx_knobs[EUPHORIA_MONO_FX_GROUPS_COUNT][
        EUPHORIA_MONO_FX_COUNT][EUPHORIA_CONTROLS_PER_MOD_EFFECT];
    PYFX_Data *mfx_comboboxes[EUPHORIA_MONO_FX_GROUPS_COUNT][
        EUPHORIA_MONO_FX_COUNT];

    PYFX_Data *master_pitch;
    PYFX_Data *adsr_lin_main;
    PYFX_Data *attack;
    PYFX_Data *decay;
    PYFX_Data *sustain;
    PYFX_Data *release;

    PYFX_Data *attack_f;
    PYFX_Data *decay_f;
    PYFX_Data *sustain_f;
    PYFX_Data *release_f;

    PYFX_Data *master_vol;

    PYFX_Data *master_glide;
    PYFX_Data *master_pb_amt;

    PYFX_Data *pitch_env_time;

    PYFX_Data *lfo_freq;
    PYFX_Data *lfo_type;
    PYFX_Data *lfo_pitch;
    PYFX_Data *lfo_pitch_fine;

    PYFX_Data *min_note;
    PYFX_Data *max_note;

    //Corresponds to the actual knobs on the effects themselves,
    //not the mod matrix
    PYFX_Data *pfx_mod_knob[EUPHORIA_MODULAR_POLYFX_COUNT][
        EUPHORIA_CONTROLS_PER_MOD_EFFECT];

    PYFX_Data *fx_combobox[EUPHORIA_MODULAR_POLYFX_COUNT];

    //PolyFX Mod Matrix
    //Corresponds to the mod matrix spinboxes
    PYFX_Data *polyfx_mod_matrix[EUPHORIA_MODULAR_POLYFX_COUNT][
        EUPHORIA_MODULATOR_COUNT][EUPHORIA_CONTROLS_PER_MOD_EFFECT];

    //End from PolyFX Mod Matrix

    //These 2 calculate which channels are assigned to a sample
    //and should be processed
    int monofx_channel_index[EUPHORIA_MONO_FX_GROUPS_COUNT];
    int monofx_channel_index_count;
    //Tracks which indexes are in use
    int monofx_channel_index_tracker[EUPHORIA_MONO_FX_GROUPS_COUNT];
    //The MonoFX group selected for each sample
    PYFX_Data *sample_mfx_groups[EUPHORIA_MONO_FX_GROUPS_COUNT];
    int sample_mfx_groups_index[EUPHORIA_MONO_FX_GROUPS_COUNT];
    /*TODO:  Deprecate these 2?*/
    int loaded_samples[EUPHORIA_MAX_SAMPLE_COUNT];
    int loaded_samples_count;
    /*Used as a boolean when determining if a sample has already been loaded*/
    int sample_is_loaded;
    /*The index of the current sample being played*/
    int current_sample;

    float ratio;
    t_voc_voices * voices;
    long         sampleNo;

    float sample[2];

    t_euphoria_mono_modules * mono_modules;
    t_pit_ratio * smp_pit_ratio;
    t_euphoria_poly_voice * data[EUPHORIA_POLYPHONY];

    //These are used for storing the mono FX buffers from the polyphonic voices.
    float mono_fx_buffers[EUPHORIA_MONO_FX_GROUPS_COUNT][2];
    //For indexing operations that don't need to track realtime events closely
    int i_slow_index;

    float amp;  //linear amplitude, from the master volume knob

    float sv_pitch_bend_value;
    float sv_last_note;  //For glide

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    float * port_table;
    int plugin_uid;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_euphoria __attribute__((aligned(16)));



#endif
