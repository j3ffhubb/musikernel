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

#ifndef MULTIFX3KNOB_H
#define	MULTIFX3KNOB_H

/*This is actually count, not index TODO:  Rename*/
#define MULTIFX3KNOB_MAX_INDEX 30
#define MULTIFX3KNOB_KNOB_COUNT 3

#include "../filter/svf_stereo.h"
#include "../filter/comb_filter.h"
#include "../distortion/clipper.h"
#include "../signal_routing/audio_xfade.h"
#include "../../lib/amp.h"
#include "../signal_routing/amp_and_panner.h"
#include "../filter/peak_eq.h"
#include "../dynamics/limiter.h"
#include "../distortion/saturator.h"
#include "../filter/formant_filter.h"
#include "../delay/chorus.h"
#include "../distortion/glitch.h"
#include "../distortion/ring_mod.h"
#include "../distortion/lofi.h"
#include "../distortion/sample_and_hold.h"
#include "../distortion/foldback.h"

#ifdef	__cplusplus
extern "C" {
#endif

/*BIG TODO:  Add a function to modify for the modulation sources*/

typedef struct
{
    int effect_index;
    int channels;  //Currently only 1 or 2 are supported
    t_svf2_filter svf;
    t_comb_filter comb_filter0;
    t_comb_filter comb_filter1;
    t_pkq_peak_eq eq0;
    t_clipper clipper;
    t_lim_limiter limiter;
    t_sat_saturator saturator;
    float output0, output1;
    float control[MULTIFX3KNOB_KNOB_COUNT];
    float control_value[MULTIFX3KNOB_KNOB_COUNT];
    float mod_value[MULTIFX3KNOB_KNOB_COUNT];
    t_audio_xfade xfader;
    t_amp_and_panner amp_and_panner;
    float outgain;  //For anything with an outgain knob
    t_for_formant_filter formant_filter;
    t_crs_chorus chorus;
    t_glc_glitch glitch;
    t_rmd_ring_mod ring_mod;
    t_lfi_lofi lofi;
    t_sah_sample_and_hold s_and_h;
    t_grw_growl_filter growl_filter;
    t_fbk_foldback foldback;
}t_mf3_multi;

/*A function pointer for switching between effect types*/
typedef void (*fp_mf3_run)(t_mf3_multi*,float,float);

inline void v_mf3_set(t_mf3_multi*,float,float,float);
inline void v_mf3_mod(t_mf3_multi*,float,float,float,float);
inline void v_mf3_mod_single(t_mf3_multi*,float,float, int);
inline void v_mf3_commit_mod(t_mf3_multi*);
inline void v_mf3_run_off(t_mf3_multi*,float,float);
inline void v_mf3_run_lp2(t_mf3_multi*,float,float);
inline void v_mf3_run_lp4(t_mf3_multi*,float,float);
inline void v_mf3_run_hp2(t_mf3_multi*,float,float);
inline void v_mf3_run_hp4(t_mf3_multi*,float,float);
inline void v_mf3_run_bp2(t_mf3_multi*,float,float);
inline void v_mf3_run_bp4(t_mf3_multi*,float,float);
inline void v_mf3_run_notch2(t_mf3_multi*,float,float);
inline void v_mf3_run_notch4(t_mf3_multi*,float,float);
inline void v_mf3_run_eq(t_mf3_multi*,float,float);
inline void v_mf3_run_dist(t_mf3_multi*,float,float);
inline void v_mf3_run_comb(t_mf3_multi*,float,float);
inline void v_mf3_run_amp_panner(t_mf3_multi*,float,float);
inline void v_mf3_run_limiter(t_mf3_multi*,float,float);
inline void v_mf3_run_saturator(t_mf3_multi*, float, float);
inline void v_mf3_run_formant_filter(t_mf3_multi*, float, float);
inline void v_mf3_run_chorus(t_mf3_multi*, float, float);
inline void v_mf3_run_glitch(t_mf3_multi*, float, float);
inline void v_mf3_run_ring_mod(t_mf3_multi*, float, float);
inline void v_mf3_run_lofi(t_mf3_multi*, float, float);
inline void v_mf3_run_s_and_h(t_mf3_multi*, float, float);
inline void v_mf3_run_hp_dw(t_mf3_multi*,float,float);
inline void v_mf3_run_lp_dw(t_mf3_multi*,float,float);
inline void v_mf3_run_monofier(t_mf3_multi*,float,float);
inline void v_mf3_run_lp_hp(t_mf3_multi*,float,float);
inline void v_mf3_run_growl_filter(t_mf3_multi*,float,float);
inline void v_mf3_run_screech_lp(t_mf3_multi*,float,float);
inline void v_mf3_run_metal_comb(t_mf3_multi*,float,float);
inline void v_mf3_run_notch_dw(t_mf3_multi*,float,float);
inline void v_mf3_run_foldback(t_mf3_multi*,float,float);

inline void f_mfx_transform_svf_filter(t_mf3_multi*);

//inline float f_mf3_midi_to_pitch(float);

t_mf3_multi * g_mf3_get(float);
void v_mf3_free(t_mf3_multi*);
inline fp_mf3_run g_mf3_get_function_pointer( int);

const fp_mf3_run mf3_function_pointers[MULTIFX3KNOB_MAX_INDEX] =
{
        v_mf3_run_off, //0
        v_mf3_run_lp2, //1
        v_mf3_run_lp4, //2
        v_mf3_run_hp2, //3
        v_mf3_run_hp4, //4
        v_mf3_run_bp2, //5
        v_mf3_run_bp4, //6
        v_mf3_run_notch2, //7
        v_mf3_run_notch4, //8
        v_mf3_run_eq, //9
        v_mf3_run_dist, //10
        v_mf3_run_comb, //11
        v_mf3_run_amp_panner, //12
        v_mf3_run_limiter, //13
        v_mf3_run_saturator, //14
        v_mf3_run_formant_filter, //15
        v_mf3_run_chorus, //16
        v_mf3_run_glitch, //17
        v_mf3_run_ring_mod, //18
        v_mf3_run_lofi, //19
        v_mf3_run_s_and_h, //20
        v_mf3_run_lp_dw, //21
        v_mf3_run_hp_dw, //22
        v_mf3_run_monofier, //23
        v_mf3_run_lp_hp, //24
        v_mf3_run_growl_filter, //25
        v_mf3_run_screech_lp, //26
        v_mf3_run_metal_comb,   //27
        v_mf3_run_notch_dw, //28
        v_mf3_run_foldback //29
};


void v_mf3_reset_null(t_mf3_multi*);
void v_mf3_reset_svf(t_mf3_multi*);
void v_mf3_reset_glitch(t_mf3_multi*);


/*A function pointer for switching between effect types*/
typedef void (*fp_mf3_reset)(t_mf3_multi*);

const fp_mf3_reset mf3_reset_function_pointers[MULTIFX3KNOB_MAX_INDEX] =
{
        v_mf3_reset_null, //0
        v_mf3_reset_svf, //1
        v_mf3_reset_svf, //2
        v_mf3_reset_svf, //3
        v_mf3_reset_svf, //4
        v_mf3_reset_svf, //5
        v_mf3_reset_svf, //6
        v_mf3_reset_svf, //7
        v_mf3_reset_svf, //8
        v_mf3_reset_null, //9
        v_mf3_reset_null, //10
        v_mf3_reset_null, //11
        v_mf3_reset_null, //12
        v_mf3_reset_null, //13
        v_mf3_reset_null, //14
        v_mf3_reset_null, //15
        v_mf3_reset_null, //16
        v_mf3_reset_glitch, //17
        v_mf3_reset_null, //18
        v_mf3_reset_null, //19
        v_mf3_reset_null, //20
        v_mf3_reset_svf, //21
        v_mf3_reset_svf, //22
        v_mf3_reset_null, //23
        v_mf3_reset_svf, //24
        v_mf3_reset_null, //25
        v_mf3_reset_svf, //26
        v_mf3_reset_null, //27
        v_mf3_reset_svf, //28
        v_mf3_reset_null //29
};



void v_mf3_reset_null(t_mf3_multi* a_mf3)
{
    //do nothing
}

void v_mf3_reset_svf(t_mf3_multi* a_mf3)
{
    v_svf2_reset(&a_mf3->svf);
}

void v_mf3_reset_glitch(t_mf3_multi* a_mf3)
{
    v_glc_glitch_retrigger(&a_mf3->glitch);
}

/* void v_mf3_set(t_fx3_multi* a_mf3, int a_fx_index)
 */
inline fp_mf3_run g_mf3_get_function_pointer( int a_fx_index)
{
    return mf3_function_pointers[a_fx_index];
}

/* void v_mf3_set(t_fx3_multi* a_mf3, int a_fx_index)
 */
inline fp_mf3_reset g_mf3_get_reset_function_pointer(int a_fx_index)
{
    return mf3_reset_function_pointers[a_fx_index];
}


inline void v_mf3_set(t_mf3_multi*__restrict a_mf3, float a_control0,
        float a_control1, float a_control2)
{
    a_mf3->control[0] = a_control0;
    a_mf3->control[1] = a_control1;
    a_mf3->control[2] = a_control2;

    a_mf3->mod_value[0] = 0.0f;
    a_mf3->mod_value[1] = 0.0f;
    a_mf3->mod_value[2] = 0.0f;
}

/* inline void v_mf3_mod(t_mf3_multi* a_mf3,
 * float a_mod, //Expects 0 to 1 or -1 to 1 range from an LFO, envelope, etc...
 * float a_amt0, float a_amt1, float a_amt2)  //Amount, from the GUI.
 *                                              Range:  -100 to 100
 */
inline void v_mf3_mod(t_mf3_multi*__restrict a_mf3,float a_mod, float a_amt0,
        float a_amt1, float a_amt2)
{
    a_mf3->mod_value[0] = (a_mf3->mod_value[0]) + (a_mod * a_amt0 * .01f);
    a_mf3->mod_value[1] = (a_mf3->mod_value[1]) + (a_mod * a_amt1 * .01f);
    a_mf3->mod_value[2] = (a_mf3->mod_value[2]) + (a_mod * a_amt2 * .01f);
}

/* inline void v_mf3_mod_single(
 * t_mf3_multi* a_mf3,
 * float a_mod, //The output of the LFO, etc...  -1.0f to 1.0f
 * float a_amt, //amount, -1.0f to 1.0f
 * int a_index)  //control index
 */
inline void v_mf3_mod_single(t_mf3_multi*__restrict a_mf3,float a_mod,
        float a_amt, int a_index)
{
    //not  * .01 because it's expected you did this at note_on
    a_mf3->mod_value[a_index] = (a_mf3->mod_value[a_index]) + (a_mod * a_amt);
}

inline void v_mf3_commit_mod(t_mf3_multi*__restrict a_mf3)
{
    a_mf3->control[0] = (a_mf3->control[0]) + ((a_mf3->mod_value[0]) * 127.0f);

    if((a_mf3->control[0]) > 127.0f)
    {
        a_mf3->control[0] = 127.0f;
    }

    if((a_mf3->control[0]) < 0.0f)
    {
        a_mf3->control[0] = 0.0f;
    }

    a_mf3->control[1] = (a_mf3->control[1]) + ((a_mf3->mod_value[1]) * 127.0f);

    if((a_mf3->control[1]) > 127.0f)
    {
        a_mf3->control[1] = 127.0f;
    }

    if((a_mf3->control[1]) < 0.0f)
    {
        a_mf3->control[1] = 0.0f;
    }

    a_mf3->control[2] = (a_mf3->control[2]) + ((a_mf3->mod_value[2]) * 127.0f);

    if((a_mf3->control[2]) > 127.0f)
    {
        a_mf3->control[2] = 127.0f;
    }

    if((a_mf3->control[2]) < 0.0f)
    {
        a_mf3->control[2] = 0.0f;
    }
}

inline void v_mf3_run_off(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    a_mf3->output0 = a_in0;
    a_mf3->output1 = a_in1;
}

inline void v_mf3_run_lp2(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_2_pole_lp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_lp4(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_4_pole_lp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_hp2(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_2_pole_hp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_hp4(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_4_pole_hp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_bp2(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_2_pole_bp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_bp4(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_4_pole_bp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_notch2(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_2_pole_notch(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_notch4(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_4_pole_notch(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = a_mf3->svf.output0;
    a_mf3->output1 = a_mf3->svf.output1;
}

inline void v_mf3_run_eq(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    //cutoff
    a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.818897638f) + 20.0f);
    //width
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.039370079f) + 1.0f;
    //gain
    a_mf3->control_value[2] = (a_mf3->control[2]) * 0.377952756f - 24.0f;

    v_pkq_calc_coeffs(&a_mf3->eq0, a_mf3->control_value[0],
            a_mf3->control_value[1], a_mf3->control_value[2]);

    v_pkq_run(&a_mf3->eq0, a_in0, a_in1);

    a_mf3->output0 = (a_mf3->eq0.output0);
    a_mf3->output1 = (a_mf3->eq0.output1);
}

inline void v_mf3_run_dist(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.377952756f);
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.007874016f);
    a_mf3->control_value[2] = (((a_mf3->control[2]) * 0.236220472f) - 30.0f);
    a_mf3->outgain = f_db_to_linear(a_mf3->control_value[2]);
    v_clp_set_in_gain(&a_mf3->clipper, (a_mf3->control_value[0]));
    v_axf_set_xfade(&a_mf3->xfader, (a_mf3->control_value[1]));

    a_mf3->output0 = f_axf_run_xfade(&a_mf3->xfader, a_in0,
            (f_clp_clip(&a_mf3->clipper, a_in0))) * (a_mf3->outgain);
    a_mf3->output1 = f_axf_run_xfade(&a_mf3->xfader, a_in1,
            (f_clp_clip(&a_mf3->clipper, a_in1))) * (a_mf3->outgain);
}


inline void v_mf3_run_comb(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);

    //cutoff
    a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.692913386) + 20.0f);
    //res
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.157480315) - 20.0f;

    v_cmb_set_all(&a_mf3->comb_filter0, (a_mf3->control_value[1]),
            (a_mf3->control_value[1]), (a_mf3->control_value[0]));

    v_cmb_set_all(&a_mf3->comb_filter1, (a_mf3->control_value[1]),
            (a_mf3->control_value[1]), (a_mf3->control_value[0]));

    v_cmb_run(&a_mf3->comb_filter0, a_in0);
    v_cmb_run(&a_mf3->comb_filter1, a_in1);

    a_mf3->output0 = a_mf3->comb_filter0.output_sample;
    a_mf3->output1 = a_mf3->comb_filter1.output_sample;
}

inline void v_mf3_run_amp_panner(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);

    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.007874016f);
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.503937f) - 40.0f;

    v_app_set(&a_mf3->amp_and_panner, (a_mf3->control_value[1]),
            (a_mf3->control_value[0]));
    v_app_run(&a_mf3->amp_and_panner, a_in0, a_in1);

    a_mf3->output0 = a_mf3->amp_and_panner.output0;
    a_mf3->output1 = a_mf3->amp_and_panner.output1;
}

inline void f_mfx_transform_svf_filter(t_mf3_multi*__restrict a_mf3)
{
    v_mf3_commit_mod(a_mf3);
    //cutoff
    a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.818897638) + 20.0f);
    //res
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.236220472) - 30.0f;

    v_svf2_set_cutoff_base(&a_mf3->svf, (a_mf3->control_value[0]));
    v_svf2_set_res(&a_mf3->svf, (a_mf3->control_value[1]));
    v_svf2_set_cutoff(&a_mf3->svf);
}


inline void v_mf3_run_limiter(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.236220472f) - 30.0f);
    a_mf3->control_value[1] = (((a_mf3->control[1]) * 0.093700787f) - 11.9f);
    a_mf3->control_value[2] = (((a_mf3->control[2]) * 11.417322835f) + 50.0f);

    v_lim_set(&a_mf3->limiter, (a_mf3->control_value[0]),
            (a_mf3->control_value[1]), (a_mf3->control_value[2]));
    v_lim_run(&a_mf3->limiter, a_in0, a_in1);

    a_mf3->output0 = a_mf3->limiter.output0;
    a_mf3->output1 = a_mf3->limiter.output1;
}

inline void v_mf3_run_saturator(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.188976378) - 12.0f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.748031496f) + 5.0f;
    a_mf3->control_value[2] = ((a_mf3->control[2]) * 0.188976378) - 12.0f;

    v_sat_set(&a_mf3->saturator, (a_mf3->control_value[0]),
            (a_mf3->control_value[1]), (a_mf3->control_value[2]));

    v_sat_run(&a_mf3->saturator, a_in0, a_in1);

    a_mf3->output0 = a_mf3->saturator.output0;
    a_mf3->output1 = a_mf3->saturator.output1;
}

inline void v_mf3_run_formant_filter(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.07086f);
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.007874016f);

    v_for_formant_filter_set(&a_mf3->formant_filter, a_mf3->control_value[0],
            a_mf3->control_value[1]);
    v_for_formant_filter_run(&a_mf3->formant_filter, a_in0, a_in1);

    a_mf3->output0 = a_mf3->formant_filter.output0;
    a_mf3->output1 = a_mf3->formant_filter.output1;
}

inline void v_mf3_run_chorus(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.04488189f) + 0.3f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.1889f) - 24.0f;

    v_crs_chorus_set(&a_mf3->chorus, a_mf3->control_value[0],
            a_mf3->control_value[1]);
    v_crs_chorus_run(&a_mf3->chorus, a_in0, a_in1);

    a_mf3->output0 = a_mf3->chorus.output0;
    a_mf3->output1 = a_mf3->chorus.output1;
}

inline void v_mf3_run_glitch(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.62992126f) + 5.0f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.08661f) + 1.1f;
    a_mf3->control_value[2] = ((a_mf3->control[2]) * 0.007874016f);

    v_glc_glitch_set(&a_mf3->glitch, a_mf3->control_value[0],
            a_mf3->control_value[1], a_mf3->control_value[2]);
    v_glc_glitch_run(&a_mf3->glitch, a_in0, a_in1);

    a_mf3->output0 = a_mf3->glitch.output0;
    a_mf3->output1 = a_mf3->glitch.output1;
}

inline void v_mf3_run_ring_mod(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.44094f) + 24.0f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.007874f);

    v_rmd_ring_mod_set(
        &a_mf3->ring_mod,
        a_mf3->control_value[0],
        a_mf3->control_value[1]
    );
    v_rmd_ring_mod_run(&a_mf3->ring_mod, a_in0, a_in1);

    a_mf3->output0 = a_mf3->ring_mod.output0;
    a_mf3->output1 = a_mf3->ring_mod.output1;
}

inline void v_mf3_run_lofi(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.094488f) + 4.0f;

    v_lfi_lofi_set(&a_mf3->lofi, a_mf3->control_value[0]);
    v_lfi_lofi_run(&a_mf3->lofi, a_in0, a_in1);

    a_mf3->output0 = a_mf3->lofi.output0;
    a_mf3->output1 = a_mf3->lofi.output1;
}

inline void v_mf3_run_s_and_h(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.23622f) + 60.0f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.007874016f);

    v_sah_sample_and_hold_set(&a_mf3->s_and_h, a_mf3->control_value[0],
            a_mf3->control_value[1]);
    v_sah_sample_and_hold_run(&a_mf3->s_and_h, a_in0, a_in1);

    a_mf3->output0 = a_mf3->s_and_h.output0;
    a_mf3->output1 = a_mf3->s_and_h.output1;
}


inline void v_mf3_run_lp_dw(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    a_mf3->control_value[2] = a_mf3->control[2] * 0.007874016f;
    v_axf_set_xfade(&a_mf3->xfader, a_mf3->control_value[2]);
    v_svf2_run_2_pole_lp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = f_axf_run_xfade(&a_mf3->xfader, a_in0, a_mf3->svf.output0);
    a_mf3->output1 = f_axf_run_xfade(&a_mf3->xfader, a_in1, a_mf3->svf.output1);
}

inline void v_mf3_run_hp_dw(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    a_mf3->control_value[2] = a_mf3->control[2] * 0.007874016f;
    v_axf_set_xfade(
        &a_mf3->xfader,
        a_mf3->control_value[2]
    );
    v_svf2_run_2_pole_hp(
        &a_mf3->svf,
        a_in0,
        a_in1
    );
    a_mf3->output0 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in0,
        a_mf3->svf.output0
    );
    a_mf3->output1 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in1,
        a_mf3->svf.output1
    );
}

inline void v_mf3_run_notch_dw(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    f_mfx_transform_svf_filter(a_mf3);
    a_mf3->control_value[2] = a_mf3->control[2] * 0.007874016f;
    v_axf_set_xfade(
        &a_mf3->xfader,
        a_mf3->control_value[2]
    );
    v_svf2_run_4_pole_notch(
        &a_mf3->svf,
        a_in0,
        a_in1
    );
    a_mf3->output0 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in0,
        a_mf3->svf.output0
    );
    a_mf3->output1 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in1,
        a_mf3->svf.output1
    );
}

inline void v_mf3_run_foldback(
    t_mf3_multi*__restrict a_mf3,
    float a_in0,
    float a_in1
){
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.094488189f) - 12.0f;
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.094488189f);
    a_mf3->control_value[2] = a_mf3->control[2] * 0.007874016f;
    v_axf_set_xfade(&a_mf3->xfader, a_mf3->control_value[2]);
    v_fbk_set(&a_mf3->foldback,
        a_mf3->control_value[0], a_mf3->control_value[1]);
    v_fbk_run(&a_mf3->foldback, a_in0, a_in1);
    a_mf3->output0 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in0,
        a_mf3->foldback.output[0]
    );
    a_mf3->output1 = f_axf_run_xfade(
        &a_mf3->xfader,
        a_in1,
        a_mf3->foldback.output[1]
    );
}


inline void v_mf3_run_monofier(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    v_mf3_commit_mod(a_mf3);

    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.007874016f);
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.283464567f) - 30.0f;

    v_app_set(&a_mf3->amp_and_panner, (a_mf3->control_value[1]),
            (a_mf3->control_value[0]));
    v_app_run_monofier(&a_mf3->amp_and_panner, a_in0, a_in1);

    a_mf3->output0 = a_mf3->amp_and_panner.output0;
    a_mf3->output1 = a_mf3->amp_and_panner.output1;
}

inline void v_mf3_run_lp_hp(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    f_mfx_transform_svf_filter(a_mf3);
    a_mf3->control_value[2] = a_mf3->control[2] * 0.007874016f;
    v_axf_set_xfade(&a_mf3->xfader, a_mf3->control_value[2]);
    v_svf2_run_2_pole_lp(&a_mf3->svf, a_in0, a_in1);
    a_mf3->output0 = f_axf_run_xfade(&a_mf3->xfader,
            a_mf3->svf.filter_kernels[0][0].lp,
            a_mf3->svf.filter_kernels[0][0].hp);
    a_mf3->output1 = f_axf_run_xfade(&a_mf3->xfader,
            a_mf3->svf.filter_kernels[0][1].lp,
            a_mf3->svf.filter_kernels[0][1].hp);
}

inline void v_mf3_run_growl_filter(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    v_mf3_commit_mod(a_mf3);
    a_mf3->control_value[0] = ((a_mf3->control[0]) * 0.0390625f);
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.007874016f);
    a_mf3->control_value[2] = ((a_mf3->control[2]) * 0.15625f);

    v_grw_growl_filter_set(&a_mf3->growl_filter, a_mf3->control_value[0],
            a_mf3->control_value[1], a_mf3->control_value[2]);
    v_grw_growl_filter_run(&a_mf3->growl_filter, a_in0, a_in1);

    a_mf3->output0 = a_mf3->growl_filter.output0;
    a_mf3->output1 = a_mf3->growl_filter.output1;
}

inline void v_mf3_run_screech_lp(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    f_mfx_transform_svf_filter(a_mf3);
    v_svf2_run_4_pole_lp(&a_mf3->svf, a_in0, a_in1);

    //a_mf3->output0 = a_mf3->svf->output0;
    //a_mf3->output1 = a_mf3->svf->output1;

    v_clp_set_clip_sym(&a_mf3->clipper, -3.0f);
    v_sat_set(&a_mf3->saturator, 0.0f, 100.0f, 0.0f);
    v_sat_run(&a_mf3->saturator, a_mf3->svf.output0, a_mf3->svf.output1);

    //cutoff
    //a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.692913386) + 20.0f);
    //res
    //a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.157480315) - 24.0f;

    v_cmb_set_all(&a_mf3->comb_filter0, (a_mf3->control_value[1]),
            (a_mf3->control_value[1]), (a_mf3->control_value[0]));

    v_cmb_set_all(&a_mf3->comb_filter1, (a_mf3->control_value[1]),
            (a_mf3->control_value[1]), (a_mf3->control_value[0]));

    v_cmb_run(&a_mf3->comb_filter0,
        f_clp_clip(&a_mf3->clipper, a_mf3->saturator.output0));
    v_cmb_run(&a_mf3->comb_filter1,
        f_clp_clip(&a_mf3->clipper, a_mf3->saturator.output1));

    a_mf3->output0 = (a_mf3->saturator.output0 -
            a_mf3->comb_filter0.wet_sample);
    a_mf3->output1 = (a_mf3->saturator.output1 -
            a_mf3->comb_filter1.wet_sample);
}


inline void v_mf3_run_metal_comb(t_mf3_multi*__restrict a_mf3, float a_in0,
        float a_in1)
{
    v_mf3_commit_mod(a_mf3);

    //cutoff
    a_mf3->control_value[0] = (((a_mf3->control[0]) * 0.24) + 30.0f);
    //res
    a_mf3->control_value[1] = ((a_mf3->control[1]) * 0.157480315) - 20.0f;
    //detune
    a_mf3->control_value[2] = ((a_mf3->control[2]) * 0.02362f) + 1.0f;

    v_cmb_mc_set_all(&a_mf3->comb_filter0, (a_mf3->control_value[1]),
                    (a_mf3->control_value[0]), a_mf3->control_value[2]);

    v_cmb_mc_set_all(&a_mf3->comb_filter1, (a_mf3->control_value[1]),
            (a_mf3->control_value[0]), a_mf3->control_value[2]);

    v_cmb_mc_run(&a_mf3->comb_filter0, a_in0);
    v_cmb_mc_run(&a_mf3->comb_filter1, a_in1);

    a_mf3->output0 = (a_mf3->comb_filter0.output_sample);
    a_mf3->output1 = (a_mf3->comb_filter1.output_sample);
}

void g_mf3_init(t_mf3_multi * f_result, float a_sample_rate, int a_huge_pages)
{
    f_result->effect_index = 0;
    f_result->channels = 2;
    g_svf2_init(&f_result->svf, a_sample_rate);
    g_cmb_init(&f_result->comb_filter0, a_sample_rate, a_huge_pages);
    g_cmb_init(&f_result->comb_filter1, a_sample_rate, a_huge_pages);
    g_pkq_init(&f_result->eq0, a_sample_rate);
    g_clp_init(&f_result->clipper);
    v_clp_set_clip_sym(&f_result->clipper, -3.0f);
    g_lim_init(&f_result->limiter, a_sample_rate, a_huge_pages);
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->control[0] = 0.0f;
    f_result->control[1] = 0.0f;
    f_result->control[2] = 0.0f;
    f_result->control_value[0] = 65.0f;
    f_result->control_value[1] = 65.0f;
    f_result->control_value[2] = 65.0f;
    f_result->mod_value[0] = 0.0f;
    f_result->mod_value[1] = 0.0f;
    f_result->mod_value[2] = 0.0f;
    g_axf_init(&f_result->xfader, -3.0f);
    f_result->outgain = 1.0f;
    g_app_init(&f_result->amp_and_panner);
    g_sat_init(&f_result->saturator);
    g_for_init(&f_result->formant_filter, a_sample_rate);
    g_crs_init(&f_result->chorus, a_sample_rate, a_huge_pages);
    g_glc_init(&f_result->glitch, a_sample_rate);
    g_rmd_init(&f_result->ring_mod, a_sample_rate);
    g_lfi_init(&f_result->lofi);
    g_sah_init(&f_result->s_and_h, a_sample_rate);
    g_grw_init(&f_result->growl_filter, a_sample_rate);
    g_fbk_init(&f_result->foldback);

}

/* t_mf3_multi g_mf3_get(
 * float a_sample_rate)
 */
t_mf3_multi * g_mf3_get(float a_sample_rate)
{
    t_mf3_multi * f_result;

    lmalloc((void**)&f_result, sizeof(t_mf3_multi));
    g_mf3_init(f_result, a_sample_rate, 0);

    return f_result;
}

void v_mf3_free(t_mf3_multi * a_mf3 )
{
    if(a_mf3)
    {
        v_crs_free(&a_mf3->chorus);
        v_cmb_free(&a_mf3->comb_filter0);
        v_cmb_free(&a_mf3->comb_filter1);
        v_glc_glitch_free(&a_mf3->glitch);
        v_lim_free(&a_mf3->limiter);
        free(a_mf3);
    }
}

#ifdef	__cplusplus
}
#endif

#endif	/* MULTIFX3KNOB_H */

