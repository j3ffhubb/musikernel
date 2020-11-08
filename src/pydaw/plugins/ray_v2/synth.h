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

#ifndef RAYV2_SYNTH_H
#define	RAYV2_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"
#include "../../libmodsynth/lib/voice.h"

#define RAYV2_ATTACK  2
#define RAYV2_DECAY   3
#define RAYV2_SUSTAIN 4
#define RAYV2_RELEASE 5
#define RAYV2_TIMBRE  6
#define RAYV2_RES  7
#define RAYV2_DIST 8
#define RAYV2_FILTER_ATTACK  9
#define RAYV2_FILTER_DECAY   10
#define RAYV2_FILTER_SUSTAIN 11
#define RAYV2_FILTER_RELEASE 12
#define RAYV2_NOISE_AMP 13
#define RAYV2_FILTER_ENV_AMT 14
#define RAYV2_DIST_WET 15
#define RAYV2_OSC1_TYPE 16
#define RAYV2_OSC1_PITCH 17
#define RAYV2_OSC1_TUNE 18
#define RAYV2_OSC1_VOLUME 19
#define RAYV2_OSC2_TYPE 20
#define RAYV2_OSC2_PITCH 21
#define RAYV2_OSC2_TUNE 22
#define RAYV2_OSC2_VOLUME 23
#define RAYV2_MASTER_VOLUME 24
#define RAYV2_UNISON_VOICES1 25
#define RAYV2_UNISON_SPREAD1 26
#define RAYV2_MASTER_GLIDE 27
#define RAYV2_MASTER_PITCHBEND_AMT 28
#define RAYV2_PITCH_ENV_TIME 29
#define RAYV2_PITCH_ENV_AMT 30
#define RAYV2_LFO_FREQ 31
#define RAYV2_LFO_TYPE 32
#define RAYV2_LFO_AMP 33
#define RAYV2_LFO_PITCH 34
#define RAYV2_LFO_FILTER 35
#define RAYV2_OSC_HARD_SYNC 36
#define RAYV2_RAMP_CURVE 37
#define RAYV2_FILTER_KEYTRK 38
#define RAYV2_MONO_MODE 39
#define RAYV2_LFO_PHASE 40
#define RAYV2_LFO_PITCH_FINE 41
#define RAYV2_ADSR_PREFX 42
#define RAYV2_MIN_NOTE 43
#define RAYV2_MAX_NOTE 44
#define RAYV2_MASTER_PITCH 45
#define RAYV2_UNISON_VOICES2 46
#define RAYV2_UNISON_SPREAD2 47
#define RAYV2_NOISE_TYPE 48
#define RAYV2_FILTER_TYPE 49
#define RAYV2_FILTER_VELOCITY 50
#define RAYV2_DIST_OUTGAIN 51
#define RAYV2_OSC1_PB 52
#define RAYV2_OSC2_PB 53
#define RAYV2_DIST_TYPE 54
#define RAYV2_ADSR_LIN_MAIN 55

/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define RAYV2_COUNT 56

#define RAYV2_POLYPHONY   16
#define RAYV2_POLYPHONY_THRESH 12

typedef struct {
    int oversample;
    MKFLT os_recip;
    PYFX_Data *os_buffer;
    PYFX_Data *output0;
    PYFX_Data *output1;
    PYFX_Data *tune;
    PYFX_Data *adsr_lin_main;
    PYFX_Data *attack;
    PYFX_Data *decay;
    PYFX_Data *sustain;
    PYFX_Data *release;
    PYFX_Data *timbre;
    PYFX_Data *res;
    PYFX_Data *filter_type;
    PYFX_Data *filter_vel;
    PYFX_Data *dist;
    PYFX_Data *dist_out_gain;
    PYFX_Data *dist_wet;
    PYFX_Data *dist_type;
    PYFX_Data *master_pitch;

    PYFX_Data *attack_f;
    PYFX_Data *decay_f;
    PYFX_Data *sustain_f;
    PYFX_Data *release_f;

    PYFX_Data *osc1pitch;
    PYFX_Data *osc1tune;
    PYFX_Data *osc1type;
    PYFX_Data *osc1vol;
    PYFX_Data *osc1pb;

    PYFX_Data *osc2pitch;
    PYFX_Data *osc2tune;
    PYFX_Data *osc2type;
    PYFX_Data *osc2vol;
    PYFX_Data *osc2pb;

    PYFX_Data *filter_env_amt;
    PYFX_Data *filter_keytrk;
    PYFX_Data *master_vol;

    PYFX_Data *noise_amp;
    PYFX_Data *noise_type;

    PYFX_Data *uni_voice1;
    PYFX_Data *uni_voice2;
    PYFX_Data *uni_spread1;
    PYFX_Data *uni_spread2;
    PYFX_Data *master_glide;
    PYFX_Data *master_pb_amt;

    PYFX_Data *pitch_env_amt;
    PYFX_Data *pitch_env_time;

    PYFX_Data *lfo_freq;
    PYFX_Data *lfo_type;
    PYFX_Data *lfo_phase;
    PYFX_Data *lfo_amp;
    PYFX_Data *lfo_pitch;
    PYFX_Data *lfo_pitch_fine;
    PYFX_Data *lfo_filter;
    PYFX_Data *ramp_curve;

    PYFX_Data *sync_hard;
    PYFX_Data *adsr_prefx;
    PYFX_Data *mono_mode;
    PYFX_Data *min_note;
    PYFX_Data *max_note;

    t_rayv2_poly_voice * data[RAYV2_POLYPHONY];
    t_voc_voices * voices;
    long         sampleNo;

    MKFLT fs;
    t_rayv2_mono_modules * mono_modules;

    MKFLT sv_pitch_bend_value;
    MKFLT sv_last_note;  //For glide
    MKFLT master_vol_lin;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    MKFLT * port_table;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_rayv2;




#ifdef	__cplusplus
}
#endif

#endif	/* RAY_VSYNTH_H */
