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

#ifndef OSC_SIMPLE_H
#define	OSC_SIMPLE_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/osc_core.h"
#include "../../constants.h"
#include "../../lib/pitch_core.h"
#include "../../lib/fast_sine.h"
#include "../../lib/lmalloc.h"

#define OSC_UNISON_MAX_VOICES 7

//Used to switch between values, uses much less CPU than a switch statement
typedef MKFLT (*fp_get_osc_func_ptr)(t_osc_core*);

typedef struct
{
    MKFLT sr_recip;
    //Set this to the max number of voices, not to exceed OSC_UNISON_MAX_VOICES
    int voice_count;
    fp_get_osc_func_ptr osc_type;
    MKFLT bottom_pitch;
    MKFLT pitch_inc;
    MKFLT voice_inc [OSC_UNISON_MAX_VOICES];
    t_osc_core osc_cores [OSC_UNISON_MAX_VOICES];
    //Restart the oscillators at the same phase on each note-on
    MKFLT phases [OSC_UNISON_MAX_VOICES];
    MKFLT uni_spread;
    //Set this with unison voices to prevent excessive volume
    MKFLT last_pitch;
    MKFLT adjusted_amp;
    MKFLT current_sample;  //current output sample for the entire oscillator
    int is_resetting;  //For oscillator sync
}t_osc_simple_unison;


inline void v_osc_set_uni_voice_count(t_osc_simple_unison*, int);
inline void v_osc_set_unison_pitch(t_osc_simple_unison * a_osc_ptr,
        MKFLT a_spread, MKFLT a_pitch);
inline MKFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr);
inline MKFLT f_get_saw(t_osc_core *);
inline MKFLT f_get_sine(t_osc_core *);
inline MKFLT f_get_square(t_osc_core *);
inline MKFLT f_get_triangle(t_osc_core *);
inline MKFLT f_get_osc_off(t_osc_core *);
inline void v_osc_set_simple_osc_unison_type(t_osc_simple_unison *, int);
inline void v_osc_note_on_sync_phases(t_osc_simple_unison *);
t_osc_simple_unison * g_osc_get_osc_simple_unison(MKFLT);


/* void v_osc_set_uni_voice_count(
 * t_osc_simple_unison* a_osc_ptr,
 * int a_value) //the number of unison voices this oscillator should use
 */
inline void v_osc_set_uni_voice_count(t_osc_simple_unison* a_osc_ptr,
        int a_value)
{
    assert(a_value <= OSC_UNISON_MAX_VOICES && a_value >= 1);

    if(a_osc_ptr->voice_count != a_value)
    {
        // Force a recalculation of v_osc_set_unison_pitch
        a_osc_ptr->last_pitch = -12345.0f;
        a_osc_ptr->voice_count = a_value;
        a_osc_ptr->adjusted_amp = (1.0f / (MKFLT)(a_osc_ptr->voice_count)) +
            (((MKFLT)(a_osc_ptr->voice_count - 1)) * .06f);
    }
}


/* void v_osc_set_unison_pitch(
 * t_osc_simple_unison * a_osc_ptr,
 * MKFLT a_spread, //the total spread of the unison pitches, the distance in
 *                 //semitones from bottom pitch to top.  Typically .1 to .5
 * MKFLT a_pitch)  //the pitch of the oscillator in MIDI note number,
 *                 //typically 32 to 70
 */
inline void v_osc_set_unison_pitch(t_osc_simple_unison * a_osc_ptr,
        MKFLT a_spread, MKFLT a_pitch)
{
    if((a_osc_ptr->voice_count) == 1)
    {
        a_osc_ptr->voice_inc[0] =
            f_pit_midi_note_to_hz_fast(a_pitch) * a_osc_ptr->sr_recip;
    }
    else
    {
        int f_changed = 0;
        if(unlikely(a_spread != (a_osc_ptr->uni_spread)))
        {
            a_osc_ptr->uni_spread = a_spread;
            a_osc_ptr->bottom_pitch = -0.5f * a_spread;
            a_osc_ptr->pitch_inc = a_spread / ((MKFLT)(a_osc_ptr->voice_count));
            f_changed = 1;
        }

        if(a_pitch != a_osc_ptr->last_pitch || f_changed)
        {
            a_osc_ptr->last_pitch = a_pitch;

            register int f_i;

            for(f_i = 0; f_i < (a_osc_ptr->voice_count); ++f_i)
            {
                a_osc_ptr->voice_inc[f_i] = f_pit_midi_note_to_hz_fast(
                    (a_pitch + (a_osc_ptr->bottom_pitch) +
                    (a_osc_ptr->pitch_inc * ((MKFLT)f_i)))) *
                    (a_osc_ptr->sr_recip);
            }
        }
    }

}

/* MKFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
 *
 * Returns one sample of an oscillator's output
 */
inline MKFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
{
    register int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;
    t_osc_core *osc_core;
    const int voice_count = a_osc_ptr->voice_count;

    for(f_i = 0; f_i < voice_count; ++f_i)
    {
        osc_core = &a_osc_ptr->osc_cores[f_i];
        v_run_osc(osc_core, a_osc_ptr->voice_inc[f_i]);
        a_osc_ptr->current_sample +=  a_osc_ptr->osc_type(osc_core);
    }

    return (a_osc_ptr->current_sample) * (a_osc_ptr->adjusted_amp);
}

/* MKFLT f_osc_run_unison_osc(t_osc_simple_unison * a_osc_ptr)
 *
 * For warming up oscillators
 */
inline void f_osc_run_unison_osc_core_only(t_osc_simple_unison * a_osc_ptr)
{
    register int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;

    for(f_i = 0; f_i < (a_osc_ptr->voice_count); ++f_i)
    {
        v_run_osc(&a_osc_ptr->osc_cores[f_i], a_osc_ptr->voice_inc[f_i]);
    }
}

inline MKFLT f_osc_run_unison_osc_sync(t_osc_simple_unison * a_osc_ptr)
{
    register int f_i = 0;
    a_osc_ptr->current_sample = 0.0f;

    a_osc_ptr->is_resetting =
            v_run_osc_sync(&a_osc_ptr->osc_cores[f_i],
            (a_osc_ptr->voice_inc[f_i]));
    a_osc_ptr->current_sample =
            (a_osc_ptr->current_sample) +
            a_osc_ptr->osc_type(&a_osc_ptr->osc_cores[f_i]);

    return (a_osc_ptr->current_sample) * (a_osc_ptr->adjusted_amp);
}

inline MKFLT f_get_saw(t_osc_core * a_core)
{
    return (((a_core->output) * 2.0f) - 1.0f);
}

inline MKFLT f_get_sine(t_osc_core * a_core)
{
    //return sin((a_core->output) * PI2);
    return f_sine_fast_run((a_core->output));
}

inline MKFLT f_get_square(t_osc_core * a_core)
{
    if((a_core->output) >= 0.5f)
    {
        return 1.0f;
    }
    else
    {
        return -1.0f;
    }
}

inline MKFLT f_get_hsquare(t_osc_core * a_core)
{
    if((a_core->output) <= 0.25f)
    {
        return 1.0f;
    }
    else
    {
        return -0.33333333333f;
    }
}

inline MKFLT f_get_qsquare(t_osc_core * a_core)
{
    if((a_core->output) <= 0.125f)
    {
        return 1.0f;
    }
    else
    {
        return -0.14f;
    }
}

inline MKFLT f_get_triangle(t_osc_core * a_core)
{
    MKFLT f_ramp = ((a_core->output) * 4.0f) - 2.0f;
    if(f_ramp > 1.0f)
    {
        return 2.0f - f_ramp;
    }
    else if(f_ramp < -1.0f)
    {
        return (2.0f + f_ramp) * -1.0f;
    }
    else
    {
        return f_ramp;
    }
}


//Return zero if the oscillator is turned off.
inline MKFLT f_get_osc_off(t_osc_core * a_core)
{
    return 0.0f;
}

__thread fp_get_osc_func_ptr SIMPLE_OSC_TYPES[]
__attribute__((aligned(CACHE_LINE_SIZE))) = {
    f_get_osc_off, f_get_saw, f_get_square, f_get_triangle, f_get_sine
};

__thread fp_get_osc_func_ptr SIMPLE_OSC_TYPES_v2[]
__attribute__((aligned(CACHE_LINE_SIZE))) = {
    f_get_osc_off, f_get_saw, f_get_square, f_get_hsquare, f_get_qsquare,
    f_get_triangle, f_get_sine
};


inline void v_osc_set_simple_osc_unison_type(
        t_osc_simple_unison * a_osc_ptr, int a_index)
{
    a_osc_ptr->osc_type = SIMPLE_OSC_TYPES[a_index];
}

inline void v_osc_set_simple_osc_unison_type_v2(
        t_osc_simple_unison * a_osc_ptr, int a_index)
{
    a_osc_ptr->osc_type = SIMPLE_OSC_TYPES_v2[a_index];
}

/*Resync the oscillators at note_on to hopefully avoid phasing artifacts*/
inline void v_osc_note_on_sync_phases(t_osc_simple_unison * a_osc_ptr)
{
    register int i_sync_phases = 0;

    while(i_sync_phases < (a_osc_ptr->voice_count))
    {
        a_osc_ptr->osc_cores[i_sync_phases].output =
                a_osc_ptr->phases[i_sync_phases];
        ++i_sync_phases;
    }
}

inline void v_osc_note_on_sync_phases_hard(t_osc_simple_unison * a_osc_ptr)
{
    register int i_sync_phases = 0;

    while(i_sync_phases < (a_osc_ptr->voice_count))
    {
        a_osc_ptr->osc_cores[i_sync_phases].output = 0.0f;
        ++i_sync_phases;
    }
}

void g_osc_simple_unison_init(
        t_osc_simple_unison * f_result, MKFLT a_sample_rate)
{
    f_result->osc_type = f_get_saw;
    f_result->sr_recip = 1.0 / a_sample_rate;
    f_result->adjusted_amp = 1.0;
    f_result->bottom_pitch = -0.1;
    f_result->current_sample = 0.0;
    f_result->osc_type = f_get_osc_off;
    f_result->pitch_inc = 0.1f;
    f_result->uni_spread = 0.1f;
    f_result->voice_count = 1;
    f_result->is_resetting = 0;
    f_result->last_pitch = -12345.0f;
    v_osc_set_uni_voice_count(f_result, OSC_UNISON_MAX_VOICES);

    int f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES))
    {
        g_init_osc_core(&f_result->osc_cores[f_i]);
        ++f_i;
    }

    v_osc_set_unison_pitch(f_result, .5f, 60.0f);

    f_i = 0;

    //Prevent phasing artifacts from the oscillators starting at the same phase.
    while(f_i < 200000)
    {
        f_osc_run_unison_osc(f_result);
        ++f_i;
    }

    f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES))
    {
        f_result->phases[f_i] = f_result->osc_cores[f_i].output;
        ++f_i;
    }

    v_osc_set_unison_pitch(f_result, .2, 60.0f);

}

/* t_osc_simple_unison * g_osc_get_osc_simple_unison(MKFLT a_sample_rate)
 */
t_osc_simple_unison * g_osc_get_osc_simple_unison(MKFLT a_sample_rate)
{
    t_osc_simple_unison * f_result;
    lmalloc((void**)&f_result, sizeof(t_osc_simple_unison));
    g_osc_simple_unison_init(f_result, a_sample_rate);
    return f_result;
}

void g_osc_init_osc_simple_single(
        t_osc_simple_unison * f_result, MKFLT a_sample_rate)
{
    f_result->osc_type = f_get_saw;
    f_result->sr_recip = 1.0 / a_sample_rate;
    f_result->adjusted_amp = 1.0;
    f_result->bottom_pitch = -0.1;
    f_result->current_sample = 0.0;
    f_result->osc_type = f_get_osc_off;
    f_result->pitch_inc = 0.1f;
    f_result->uni_spread = 0.1f;
    f_result->last_pitch = -12345.0f;
    f_result->voice_count = 1;
    v_osc_set_uni_voice_count(f_result, 1);

    int f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES))
    {
        g_init_osc_core(&f_result->osc_cores[f_i]);
        ++f_i;
    }

    v_osc_set_unison_pitch(f_result, .5f, 60.0f);

    f_i = 0;

    while(f_i < (OSC_UNISON_MAX_VOICES))
    {
        f_result->phases[f_i] = 0.0f;
        ++f_i;
    }

    v_osc_set_unison_pitch(f_result, .2, 60.0f);
}

t_osc_simple_unison * g_osc_get_osc_simple_single(MKFLT a_sample_rate)
{
    t_osc_simple_unison * f_result;

    lmalloc((void**)&f_result, sizeof(t_osc_simple_unison));

    g_osc_init_osc_simple_single(f_result, a_sample_rate);

    return f_result;
}


#ifdef	__cplusplus
}
#endif

#endif	/* OSC_SIMPLE_H */

