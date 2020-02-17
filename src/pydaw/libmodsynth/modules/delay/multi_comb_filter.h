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

#ifndef MULTI_COMB_FILTER_H
#define	MULTI_COMB_FILTER_H


#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/amp.h"
#include "../../lib/lmalloc.h"
#include "../../lib/pitch_core.h"
#include "../../lib/interpolate-linear.h"
#include "../../lib/smoother-linear.h"
#include "../../lib/denormal.h"

typedef struct
{
    int buffer_size;  //The size of input_buffer
    int input_pointer;  //The index where the current sample is written to
    float delay_pointer; //
    float wet_sample;
    float output_sample;
    float feedback_db;
    float feedback_linear;
    float midi_note_number;
    float volume_recip;
    float spread;
    int comb_count;
    //How many samples, including the fractional part, to delay the signal
    float * delay_samples;
    float sr;
    float * input_buffer;
    t_lin_interpolater * linear;
    t_pit_pitch_core * pitch_core;
    t_amp * amp_ptr;
}t_mcm_multicomb;

inline void v_mcm_run(t_mcm_multicomb*,float);
inline void v_mcm_set(t_mcm_multicomb*, float,float,float);
t_mcm_multicomb * g_mcm_get(int, float);

/* v_mcm_run(
 * t_mcm_multicomb*,
 * float input value (audio sample, -1 to 1, typically)
 * );
 * This runs the filter.  You can then use the output sample in your plugin*/
inline void v_mcm_run(t_mcm_multicomb* a_cmb_ptr,float a_value)
{
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = a_value;
    a_cmb_ptr->output_sample = 0.0f;

    int f_i = 0;

    while(f_i < a_cmb_ptr->comb_count)
    {
        a_cmb_ptr->delay_pointer =
                (a_cmb_ptr->input_pointer) - (a_cmb_ptr->delay_samples[f_i]);

        if((a_cmb_ptr->delay_pointer) < 0.0f)
        {
            a_cmb_ptr->delay_pointer =
                    (a_cmb_ptr->delay_pointer) + (a_cmb_ptr->buffer_size);
        }

        a_cmb_ptr->wet_sample =
                (f_linear_interpolate_arr_wrap(a_cmb_ptr->input_buffer,
                (a_cmb_ptr->buffer_size), (a_cmb_ptr->delay_pointer),
                a_cmb_ptr->linear));

        a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] +=
                ((a_cmb_ptr->wet_sample) * (a_cmb_ptr->feedback_linear));

        a_cmb_ptr->output_sample += (a_cmb_ptr->wet_sample);

        ++f_i;
    }

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] *=
            (a_cmb_ptr->volume_recip);
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] =
        f_remove_denormal(a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)]);
    a_cmb_ptr->input_pointer = (a_cmb_ptr->input_pointer) + 1;

    if((a_cmb_ptr->input_pointer) >= (a_cmb_ptr->buffer_size))
    {
        a_cmb_ptr->input_pointer = 0;
    }
}

/*v_mcm_set(
 * t_mcm_multicomb*,
 * float feedback (decibels -20 to 0)
 * float pitch (midi note number, 20 to 120),
 * float a_spread);
 *
 * Sets all parameters of the comb filters.
 */
inline void v_mcm_set(t_mcm_multicomb* a_cmb_ptr, float a_feedback_db,
        float a_midi_note_number, float a_spread)
{
    /*Set feedback_linear, but only if it's changed since last time*/
    if((a_cmb_ptr->feedback_db) != a_feedback_db)
    {
        if(a_feedback_db > -0.1f)
        {
            a_cmb_ptr->feedback_db = -0.1f;
        }
        else
        {
            a_cmb_ptr->feedback_db = a_feedback_db;
        }

        // * -1;  //negative feedback, gives a comb-ier sound
        a_cmb_ptr->feedback_linear =
            f_db_to_linear_fast((a_cmb_ptr->feedback_db), a_cmb_ptr->amp_ptr);
    }

    if(((a_cmb_ptr->midi_note_number) != a_midi_note_number) ||
            ((a_cmb_ptr->spread) != a_spread))
    {
        a_cmb_ptr->midi_note_number = a_midi_note_number;
        a_cmb_ptr->spread = a_spread;
        float f_note = a_midi_note_number;
        int f_i = 0;
        while(f_i < a_cmb_ptr->comb_count)
        {
            a_cmb_ptr->delay_samples[f_i] =
                    f_pit_midi_note_to_samples(f_note, (a_cmb_ptr->sr),
                    a_cmb_ptr->pitch_core);
            f_note += a_spread;
            ++f_i;
        }
    }

}

/* t_mcm_multicomb * g_mcm_get(
 * int a_comb_count,
 * float a_sr) //sample rate
 */
t_mcm_multicomb * g_mcm_get(int a_comb_count, float a_sr)
{
    t_mcm_multicomb * f_result;

    lmalloc((void**)&f_result, sizeof(t_mcm_multicomb));

    //Allocate enough memory to accomodate 20hz filter frequency
    f_result->buffer_size = (int)((a_sr / 20.0f) + 300);

    buffer_alloc((void**)(&(f_result->input_buffer)),
        sizeof(float) * (f_result->buffer_size));

    int f_i = 0;

    while(f_i < (f_result->buffer_size))
    {
        f_result->input_buffer[f_i] = 0.0f;
        ++f_i;
    }

    f_result->input_pointer = 0;
    f_result->delay_pointer = 0;
    f_result->wet_sample = 0.0f;
    f_result->output_sample = 0.0f;
    f_result->feedback_db = -6.0f;
    f_result->feedback_linear = 0.5f;
    f_result->midi_note_number = 60.0f;

    f_result->volume_recip = 1.0f/(float)a_comb_count;

    lmalloc((void**)&f_result->delay_samples, sizeof(float) * a_comb_count);

    f_i = 0;
    while(f_i < a_comb_count)
    {
        f_result->delay_samples[f_i] = 150.0f + (float)f_i;
        ++f_i;
    }

    f_result->sr = a_sr;
    f_result->linear = g_lin_get();
    f_result->pitch_core = g_pit_get();
    f_result->amp_ptr = g_amp_get();
    f_result->comb_count = a_comb_count;

    v_mcm_set(f_result, -1.0f, 66.0f, 1.0f);
    v_mcm_run(f_result, 0.0f);

    return f_result;
}


#ifdef	__cplusplus
}
#endif


#endif	/* COMB_FILTER_H */

