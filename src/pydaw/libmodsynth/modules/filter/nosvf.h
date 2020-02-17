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

#ifndef PYDAW_NOSVF_H
#define	PYDAW_NOSVF_H

/* This is the same as the regular mono state variable filter,
 * except that is does not have built-in oversampling.  To use this,
 * you must have the entire signal chain oversampled, otherwise it
 * will explode at higher frequencies
 */

 /*Define filter types for changing the function pointer*/
 #define NOSVF_FILTER_TYPE_LP 0
 #define NOSVF_FILTER_TYPE_HP 1
 #define NOSVF_FILTER_TYPE_BP 2
 #define NOSVF_FILTER_TYPE_EQ 3
 #define NOSVF_FILTER_TYPE_NOTCH 4

 /*The maximum number of filter kernels to cascade.
  */
 #define NOSVF_MAX_CASCADE 3

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/pitch_core.h"
#include "../../lib/amp.h"
#include "../../lib/interpolate-linear.h"
#include "../../constants.h"
#include "../../lib/smoother-linear.h"
#include "../../lib/denormal.h"

typedef struct
{
    float bp_m1, lp_m1, hp, lp, bp;
}t_nosvf_kernel;


typedef struct
{
    //t_smoother_linear * cutoff_smoother;
    float cutoff_note, cutoff_hz, cutoff_filter, pi2_div_sr, sr,
            filter_res, filter_res_db, velocity_cutoff; //, velocity_cutoff_amt;

    float cutoff_base, cutoff_mod, cutoff_last;
    /*For the eq*/
    float gain_db, gain_linear;
    t_nosvf_kernel filter_kernels [NOSVF_MAX_CASCADE];
} t_nosvf_filter;

//Used to switch between values
typedef float (*fp_nosvf_run_filter)(t_nosvf_filter*,float);

/*The int is the number of cascaded filter kernels*/
inline fp_nosvf_run_filter nosvf_get_run_filter_ptr(int,int);

inline void v_nosvf_set_input_value(t_nosvf_filter*, t_nosvf_kernel *, float);

inline float v_nosvf_run_2_pole_lp(t_nosvf_filter*, float);
inline float v_nosvf_run_4_pole_lp(t_nosvf_filter*, float);
inline float v_nosvf_run_6_pole_lp(t_nosvf_filter*, float);

inline float v_nosvf_run_2_pole_hp(t_nosvf_filter*, float);
inline float v_nosvf_run_4_pole_hp(t_nosvf_filter*, float);

inline float v_nosvf_run_2_pole_bp(t_nosvf_filter*, float);
inline float v_nosvf_run_4_pole_bp(t_nosvf_filter*, float);

inline float v_nosvf_run_2_pole_notch(t_nosvf_filter*, float);
inline float v_nosvf_run_4_pole_notch(t_nosvf_filter*, float);

inline float v_nosvf_run_2_pole_eq(t_nosvf_filter*, float);
inline float v_nosvf_run_4_pole_eq(t_nosvf_filter*, float);

inline float v_nosvf_run_no_filter(t_nosvf_filter*, float);

inline float v_nosvf_run_2_pole_allpass(t_nosvf_filter*, float);

inline void v_nosvf_set_eq(t_nosvf_filter*, float);
inline void v_nosvf_set_eq4(t_nosvf_filter*, float);

inline void v_nosvf_reset(t_nosvf_filter*);

inline void v_nosvf_reset(t_nosvf_filter * a_svf)
{
    register int f_i = 0;
    while(f_i < NOSVF_MAX_CASCADE)
    {
        a_svf->filter_kernels[f_i].bp = 0.0f;
        a_svf->filter_kernels[f_i].bp_m1 = 0.0f;
        a_svf->filter_kernels[f_i].hp = 0.0f;
        a_svf->filter_kernels[f_i].lp = 0.0f;
        a_svf->filter_kernels[f_i].lp_m1 = 0.0f;
        ++f_i;
    }
}

__thread fp_nosvf_run_filter NOSVF_TYPES[9]
__attribute__((aligned(CACHE_LINE_SIZE))) = {
    v_nosvf_run_2_pole_lp,
    v_nosvf_run_4_pole_lp,
    v_nosvf_run_2_pole_hp,
    v_nosvf_run_4_pole_hp,
    v_nosvf_run_2_pole_bp,
    v_nosvf_run_4_pole_bp,
    v_nosvf_run_2_pole_notch,
    v_nosvf_run_4_pole_notch,
    v_nosvf_run_no_filter
};

/* inline float v_nosvf_run_no_filter(
 * t_nosvf_filter* a_svf,
 * float a_in) //audio input
 *
 * This is for allowing a filter to be turned off by running a
 * function pointer.  a_in is returned unmodified.
 */
inline float v_nosvf_run_no_filter(
    t_nosvf_filter* a_svf, float a_in)
{
    return a_in;
}

inline void v_nosvf_set_eq(t_nosvf_filter* a_svf, float a_gain)
{
    if(a_gain != (a_svf->gain_db))
    {
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast(a_gain);
    }
}

inline void v_nosvf_set_eq4(t_nosvf_filter* a_svf,
        float a_gain)
{
    if(a_gain != (a_svf->gain_db))
    {
        a_svf->gain_db = a_gain;
        a_svf->gain_linear = f_db_to_linear_fast((a_gain * .05));
    }
}

void g_nosvf_filter_kernel_init(t_nosvf_kernel * f_result)
{
    f_result->bp = 0.0f;
    f_result->hp = 0.0f;
    f_result->lp = 0.0f;
    f_result->lp_m1 = 0.0f;
    f_result->bp_m1 = 0.0f;
}

/* inline fp_nosvf_run_filter nosvf_get_run_filter_ptr(
 * int a_cascades,
 * int a_filter_type)
 *
 * The int refers to the number of cascaded filter kernels,
 * ie:  a value of 2 == 4 pole filter
 *
 * Filter types:
 *
 * NOSVF_FILTER_TYPE_LP 0
 * NOSVF_FILTER_TYPE_HP 1
 * NOSVF_FILTER_TYPE_BP 2
 */
inline fp_nosvf_run_filter nosvf_get_run_filter_ptr(int a_cascades, int a_filter_type)
{
    /*Lowpass*/
    if((a_cascades == 1) && (a_filter_type == NOSVF_FILTER_TYPE_LP))
    {
        return v_nosvf_run_2_pole_lp;
    }
    else if((a_cascades == 2) && (a_filter_type == NOSVF_FILTER_TYPE_LP))
    {
        return v_nosvf_run_4_pole_lp;
    }
    /*Highpass*/
    else if((a_cascades == 1) && (a_filter_type == NOSVF_FILTER_TYPE_HP))
    {
        return v_nosvf_run_2_pole_hp;
    }
    else if((a_cascades == 2) && (a_filter_type == NOSVF_FILTER_TYPE_HP))
    {
        return v_nosvf_run_4_pole_hp;
    }
    /*Bandpass*/
    else if((a_cascades == 1) && (a_filter_type == NOSVF_FILTER_TYPE_BP))
    {
        return v_nosvf_run_2_pole_bp;
    }
    else if((a_cascades == 2) && (a_filter_type == NOSVF_FILTER_TYPE_BP))
    {
        return v_nosvf_run_4_pole_bp;
    }
    /*Notch*/
    else if((a_cascades == 1) && (a_filter_type == NOSVF_FILTER_TYPE_NOTCH))
    {
        return v_nosvf_run_2_pole_notch;
    }
    else if((a_cascades == 2) && (a_filter_type == NOSVF_FILTER_TYPE_NOTCH))
    {
        return v_nosvf_run_4_pole_notch;
    }
    /*EQ*/
    else if((a_cascades == 1) && (a_filter_type == NOSVF_FILTER_TYPE_EQ))
    {
        return v_nosvf_run_2_pole_eq;
    }
    else if((a_cascades == 2) && (a_filter_type == NOSVF_FILTER_TYPE_EQ))
    {
        return v_nosvf_run_4_pole_eq;
    }
    /*This means that you entered invalid settings*/
    else
    {
        return v_nosvf_run_2_pole_lp;
    }
}

/* inline void v_nosvf_set_input_value(
 * t_nosvf_filter * a_svf,
 * t_nosvf_kernel * a_kernel,
 * float a_input_value) //the audio input to filter
 *
 * The main action to run the filter kernel*/
inline void v_nosvf_set_input_value(t_nosvf_filter * a_svf,
        t_nosvf_kernel *  a_kernel, float a_input_value)
{
    a_kernel->hp = a_input_value -
        (((a_kernel->bp_m1) * (a_svf->filter_res)) + (a_kernel->lp_m1));
    a_kernel->bp = ((a_kernel->hp) * (a_svf->cutoff_filter)) +
            (a_kernel->bp_m1);
    a_kernel->lp = ((a_kernel->bp) * (a_svf->cutoff_filter)) +
            (a_kernel->lp_m1);

    a_kernel->bp_m1 = f_remove_denormal((a_kernel->bp));
    a_kernel->lp_m1 = f_remove_denormal((a_kernel->lp));
}

inline float v_nosvf_run_2_pole_lp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].lp);
}


inline float v_nosvf_run_4_pole_lp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (a_svf->filter_kernels[0].lp));

    return (a_svf->filter_kernels[1].lp);
}

inline float v_nosvf_run_6_pole_lp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
        (a_svf->filter_kernels[0].lp));
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[2],
        (a_svf->filter_kernels[1].lp));

    return (a_svf->filter_kernels[2].lp);
}

inline float v_nosvf_run_2_pole_hp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    return (a_svf->filter_kernels[0].hp);
}


inline float v_nosvf_run_4_pole_hp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (a_svf->filter_kernels[0].hp));

    return (a_svf->filter_kernels[1].hp);
}


inline float v_nosvf_run_2_pole_bp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].bp);
}

inline float v_nosvf_run_4_pole_bp(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (a_svf->filter_kernels[0].bp));

    return (a_svf->filter_kernels[1].bp);
}

inline float v_nosvf_run_2_pole_notch(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp);
}

inline float v_nosvf_run_4_pole_notch(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp));

    return (a_svf->filter_kernels[1].hp) + (a_svf->filter_kernels[1].lp);
}

inline float v_nosvf_run_2_pole_allpass(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (a_svf->filter_kernels[0].hp) + (a_svf->filter_kernels[0].lp) +
            (a_svf->filter_kernels[0].bp);
}

inline float v_nosvf_run_2_pole_eq(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);

    return (((a_svf->filter_kernels[0].lp) + (a_svf->filter_kernels[0].hp)) +
            ((a_svf->filter_kernels[0].bp) * (a_svf->gain_linear)));
}


inline float v_nosvf_run_4_pole_eq(t_nosvf_filter* a_svf,
        float a_input)
{
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[0], a_input);
    v_nosvf_set_input_value(a_svf, &a_svf->filter_kernels[1],
            (((a_svf->filter_kernels[0].lp) + (a_svf->filter_kernels[0].hp)) +
            ((a_svf->filter_kernels[0].bp) * (a_svf->gain_linear))));

    return (((a_svf->filter_kernels[1].lp) + (a_svf->filter_kernels[1].hp)) +
            ((a_svf->filter_kernels[1].bp) * (a_svf->gain_linear)));
}

inline void v_nosvf_set_cutoff(t_nosvf_filter*);
void v_nosvf_set_res(t_nosvf_filter*,  float);
t_nosvf_filter * g_nosvf_get(float);
inline void v_nosvf_set_cutoff_base(t_nosvf_filter*, float);
inline void v_nosvf_add_cutoff_mod(t_nosvf_filter*, float);
inline void v_nosvf_velocity_mod(t_nosvf_filter*, float, float);

/* inline void v_nosvf_velocity_mod(t_nosvf_filter* a_svf, float a_velocity)
 */
inline void v_nosvf_velocity_mod(t_nosvf_filter* a_svf,
        float a_velocity, float a_amt)
{
    a_velocity *= 0.007874016f;
    a_svf->velocity_cutoff = ((a_velocity * 24.0f) - 24.0f) * a_amt;
}

/* inline void v_nosvf_set_cutoff_base(
 * t_nosvf_filter* a_svf, float a_midi_note_number)
 * Set the base pitch of the filter*/
inline void v_nosvf_set_cutoff_base(t_nosvf_filter* a_svf,
        float a_midi_note_number)
{
    a_svf->cutoff_base = a_midi_note_number;
}

/* inline void v_nosvf_add_cutoff_mod(
 * t_nosvf_filter* a_svf, float a_midi_note_number)
 * Modulate the filters cutoff with an envelope, LFO, etc...*/
inline void v_nosvf_add_cutoff_mod(t_nosvf_filter* a_svf,
        float a_midi_note_number)
{
    a_svf->cutoff_mod = (a_svf->cutoff_mod) + a_midi_note_number;
}

/* inline void v_nosvf_set_cutoff(t_nosvf_filter * a_svf)
 * This should be called every sample, otherwise the smoothing and
 * modulation doesn't work properly*/
inline void v_nosvf_set_cutoff(t_nosvf_filter * a_svf)
{
    a_svf->cutoff_note = a_svf->cutoff_base + a_svf->cutoff_mod  +
        a_svf->velocity_cutoff;
    a_svf->cutoff_mod = 0.0f;

    if(a_svf->cutoff_note > 123.9209f)  //21000hz
    {
        a_svf->cutoff_note = 123.9209f;
    }

    /*It hasn't changed since last time, return*/
    if((a_svf->cutoff_note) == (a_svf->cutoff_last))
        return;

    a_svf->cutoff_last = (a_svf->cutoff_note);

    a_svf->cutoff_hz = f_pit_midi_note_to_hz_fast(a_svf->cutoff_note);
    //_svf->cutoff_smoother->last_value);

    a_svf->cutoff_filter = (a_svf->pi2_div_sr) * (a_svf->cutoff_hz);

    /*prevent the filter from exploding numerically,
     * this does artificially cap the cutoff frequency to below what you
     * set it to if you lower the oversampling rate of the filter.*/
    if((a_svf->cutoff_filter) > 0.8f)
        a_svf->cutoff_filter = 0.8f;
}

/* void v_nosvf_set_res(
 * t_nosvf_filter * a_svf,
 * float a_db)   //-100 to 0 is the expected range
 *
 */
void v_nosvf_set_res(t_nosvf_filter * a_svf, float a_db)
{
    /*Don't calculate it again if it hasn't changed*/
    if((a_svf->filter_res_db) == a_db)
    {
        return;
    }

    a_svf->filter_res_db = a_db;

    if(a_db < -100.0f)
    {
        a_db = -100.0f;
    }
    else if (a_db > -0.2f)
    {
        a_db = -0.2f;
    }

    a_svf->filter_res = (1.0f - (f_db_to_linear_fast(a_db))) * 2.0f;
}

void g_nosvf_init(t_nosvf_filter * f_svf, float a_sample_rate)
{
    f_svf->sr = a_sample_rate;
    f_svf->pi2_div_sr = (PI2 / (f_svf->sr));

    int f_i = 0;

    while(f_i < NOSVF_MAX_CASCADE)
    {
        g_nosvf_filter_kernel_init(&f_svf->filter_kernels[f_i]);
        ++f_i;
    }

    f_svf->cutoff_note = 60.0f;
    f_svf->cutoff_hz = 1000.0f;
    f_svf->cutoff_filter = 0.7f;
    f_svf->filter_res = 0.25f;

    f_svf->cutoff_base = 78.0f;
    f_svf->cutoff_mod = 0.0f;
    f_svf->cutoff_last = 81.0f;
    f_svf->filter_res_db = -21023.0f;
    f_svf->filter_res = 0.5f;
    f_svf->velocity_cutoff = 0.0f;

    f_svf->gain_db = 0.0f;
    f_svf->gain_linear = 1.0f;

    v_nosvf_set_cutoff_base(f_svf, 75.0f);
    v_nosvf_add_cutoff_mod(f_svf, 0.0f);
    v_nosvf_set_res(f_svf, -12.0f);
    v_nosvf_set_cutoff(f_svf);
}

/* t_nosvf_filter * g_nosvf_get(float a_sample_rate)
 */
t_nosvf_filter * g_nosvf_get(float a_sample_rate)
{
    t_nosvf_filter * f_svf;
    lmalloc((void**)&f_svf, sizeof(t_nosvf_filter));
    g_nosvf_init(f_svf, a_sample_rate);
    return f_svf;
}


#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_NOSVF_H */
