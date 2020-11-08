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

#ifndef COMB_FILTER_H
#define	COMB_FILTER_H


#include "../../lib/amp.h"
#include "../../lib/pitch_core.h"
#include "../../lib/interpolate-linear.h"
#include "../../lib/smoother-linear.h"
#include "../../lib/denormal.h"
#include "../../lib/lmalloc.h"

#define MC_CMB_COUNT 4

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct st_comb_filter
{
    MKFLT delay_pointer;
    int input_pointer;  //The index where the current sample is written to
    int buffer_size;  //The size of input_buffer
    MKFLT wet_sample;
    MKFLT feedback_linear;
    MKFLT wet_db;
    MKFLT output_sample;
    MKFLT wet_linear;
    MKFLT feedback_db;
    MKFLT midi_note_number;
    //How many samples, including the fractional part, to delay the signal
    MKFLT delay_samples;
    MKFLT sr;
    MKFLT * input_buffer;
    int mc_delay_samples[MC_CMB_COUNT];
    MKFLT mc_detune;
}t_comb_filter;

inline void v_cmb_run(t_comb_filter*, MKFLT);
inline void v_cmb_set_all(t_comb_filter*, MKFLT, MKFLT, MKFLT);
void v_cmb_free(t_comb_filter*);

#ifdef	__cplusplus
}
#endif

/* v_cmb_run(
 * t_comb_filter*,
 * MKFLT input value (audio sample, -1 to 1, typically)
 * );
 * This runs the filter.  You can then use the output sample in your plugin*/
inline void v_cmb_run(t_comb_filter* a_cmb_ptr, MKFLT a_value)
{
    a_cmb_ptr->delay_pointer =
        (a_cmb_ptr->input_pointer) - (a_cmb_ptr->delay_samples);

    if((a_cmb_ptr->delay_pointer) < 0.0f)
    {
        a_cmb_ptr->delay_pointer =
            (a_cmb_ptr->delay_pointer) + (a_cmb_ptr->buffer_size);
    }

    a_cmb_ptr->wet_sample =
        (f_linear_interpolate_ptr_wrap(a_cmb_ptr->input_buffer,
        (a_cmb_ptr->buffer_size), (a_cmb_ptr->delay_pointer)));

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] =
        f_remove_denormal(a_value + ((a_cmb_ptr->wet_sample) *
        (a_cmb_ptr->feedback_linear)));

    if(unlikely((a_cmb_ptr->wet_db) <= -20.0f))
    {
        a_cmb_ptr->output_sample = a_value;
    }
    else
    {
        a_cmb_ptr->output_sample =
            (a_value + ((a_cmb_ptr->wet_sample) * (a_cmb_ptr->wet_linear)));
    }

    ++a_cmb_ptr->input_pointer;

    if(unlikely(a_cmb_ptr->input_pointer >= a_cmb_ptr->buffer_size))
    {
        a_cmb_ptr->input_pointer = 0;
    }
}

inline void v_cmb_mc_run(t_comb_filter* a_cmb_ptr, MKFLT a_value)
{
    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] = a_value;
    a_cmb_ptr->output_sample = a_value;

    if((a_cmb_ptr->wet_db) > -20.0f)
    {
        register int f_i = 0;
        while(f_i < MC_CMB_COUNT)
        {
            a_cmb_ptr->delay_pointer =
                (a_cmb_ptr->input_pointer) - (a_cmb_ptr->mc_delay_samples[f_i]);

            if((a_cmb_ptr->delay_pointer) < 0.0f)
            {
                a_cmb_ptr->delay_pointer =
                    (a_cmb_ptr->delay_pointer) + (a_cmb_ptr->buffer_size);
            }

            a_cmb_ptr->wet_sample =
                (f_linear_interpolate_ptr_wrap(a_cmb_ptr->input_buffer,
                (a_cmb_ptr->buffer_size), (a_cmb_ptr->delay_pointer)));

            a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] +=
                    ((a_cmb_ptr->wet_sample) * (a_cmb_ptr->feedback_linear));

            a_cmb_ptr->output_sample +=
                ((a_cmb_ptr->wet_sample) * (a_cmb_ptr->wet_linear));

            ++f_i;
        }
    }

    ++a_cmb_ptr->input_pointer;

    if((a_cmb_ptr->input_pointer) >= (a_cmb_ptr->buffer_size))
    {
        a_cmb_ptr->input_pointer = 0;
    }

    a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)] =
        f_remove_denormal(a_cmb_ptr->input_buffer[(a_cmb_ptr->input_pointer)]);
}

/*v_cmb_set_all(
 * t_comb_filter*,
 * MKFLT wet (decibels -20 to 0)
 * MKFLT feedback (decibels -20 to 0)
 * MKFLT pitch (midi note number, 20 to 120)
 * );
 *
 * Sets all parameters of the comb filter.
 */
inline void v_cmb_set_all(t_comb_filter* a_cmb_ptr,
    MKFLT a_wet_db, MKFLT a_feedback_db, MKFLT a_midi_note_number)
{
    if((a_cmb_ptr->wet_db) != a_wet_db)
    {
        a_cmb_ptr->wet_db = a_wet_db;
        a_cmb_ptr->wet_linear = f_db_to_linear_fast(a_wet_db);
    }

    if((a_cmb_ptr->feedback_db) != a_feedback_db)
    {
        a_cmb_ptr->feedback_db = a_feedback_db;

        if(a_feedback_db > -0.05f)
        {
            a_feedback_db = -0.05f;
        }

        a_cmb_ptr->feedback_linear = f_db_to_linear_fast(a_feedback_db);
    }

    if((a_cmb_ptr->midi_note_number) != a_midi_note_number)
    {
        a_cmb_ptr->midi_note_number = a_midi_note_number;
        a_cmb_ptr->delay_samples =
            f_pit_midi_note_to_samples(a_midi_note_number, (a_cmb_ptr->sr));
    }

}

inline void v_cmb_mc_set_all(t_comb_filter* a_cmb,
    MKFLT a_wet_db, MKFLT a_midi_note_number, MKFLT a_detune)
{
    if(a_cmb->mc_detune != a_detune ||
        a_cmb->midi_note_number != a_midi_note_number)
    {
        a_cmb->mc_detune = a_detune;
        register int f_i = 0;

        while(f_i < MC_CMB_COUNT)
        {
            a_cmb->mc_delay_samples[f_i] = f_pit_midi_note_to_samples(
                    a_midi_note_number + (a_detune * (MKFLT)f_i), (a_cmb->sr));
            ++f_i;
        }
    }

    v_cmb_set_all(a_cmb, a_wet_db, a_wet_db - 13.0f, a_midi_note_number);
}

void g_cmb_init(t_comb_filter * f_result, MKFLT a_sr, int a_huge_pages)
{
    register int f_i = 0;

    //Allocate enough memory to accomodate 20hz filter frequency
    f_result->buffer_size = (int)((a_sr / 20.0f) + 300);

    if(a_huge_pages)
    {
        hpalloc((void**)(&(f_result->input_buffer)),
            sizeof(MKFLT) * (f_result->buffer_size));
    }
    else
    {
        lmalloc((void**)(&(f_result->input_buffer)),
            sizeof(MKFLT) * (f_result->buffer_size));
    }

    while(f_i < (f_result->buffer_size))
    {
        f_result->input_buffer[f_i] = 0.0f;
        ++f_i;
    }

    f_result->input_pointer = 0;
    f_result->delay_pointer = 0;
    f_result->wet_sample = 0.0f;
    f_result->output_sample = 0.0f;
    f_result->wet_db = -1.0f;
    f_result->wet_linear = .75f;
    f_result->feedback_db = -6.0f;
    f_result->feedback_linear = 0.5f;
    f_result->midi_note_number = 60.0f;
    f_result->delay_samples = 150.0f;
    f_result->sr = a_sr;
    f_result->mc_detune = 999.999f;


    v_cmb_set_all(f_result,-6.0f, -6.0f, 66.0f);
    v_cmb_run(f_result, 0.0f);
}

void v_cmb_free(t_comb_filter * a_cmb)
{
    free(a_cmb->input_buffer);
    //free(a_cmb);
}

#endif	/* COMB_FILTER_H */

