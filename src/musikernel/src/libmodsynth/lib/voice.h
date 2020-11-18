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

#ifndef VOICE_H
#define	VOICE_H

#define VOICES_MAX_MIDI_NOTE_NUMBER 128
#define MIDI_NOTES  128

#ifdef	__cplusplus
extern "C" {
#endif

typedef enum
{
    note_state_off = 0,
    note_state_running,
    /*Synths should iterate voices looking for any voice note_state
     * that is set to releasing, and  trigger a release event in
     * it's amplitude envelope*/
    note_state_releasing,
    note_state_killed
} note_state;

typedef struct
{
    int voice_number;
    int note;
    note_state n_state;
    long on;
    long off;
}t_voc_single_voice;

typedef struct
{
    t_voc_single_voice * voices;
    int count;
    int thresh;  //when to start agressively killing voices
    int poly_mode;  //0 = retrigger, 1 = free, 2 = mono, 3 = mono_v2
}t_voc_voices;

t_voc_voices * g_voc_get_voices(int, int);

#ifdef	__cplusplus
}
#endif


void g_voc_single_init(t_voc_single_voice * f_result, int a_voice_number)
{
    f_result->voice_number = a_voice_number;
    f_result->note = -1;
    f_result->n_state = note_state_off;
    f_result->on = -1;
    f_result->off = -1;
}

t_voc_voices * g_voc_get_voices(int a_count, int a_thresh)
{
    assert(a_thresh < a_count);

    t_voc_voices * f_result;
    hpalloc((void**)&f_result, sizeof(t_voc_voices));

    f_result->count = a_count;
    f_result->thresh = a_thresh;
    f_result->poly_mode = 0;

    hpalloc((void**)&f_result->voices, sizeof(t_voc_single_voice) * a_count);

    register int f_i = 0;

    while(f_i < a_count)
    {
        g_voc_single_init(&f_result->voices[f_i], f_i);
        ++f_i;
    }

    return f_result;
}

static inline int i_get_oldest_voice(t_voc_voices *data, int a_running,
        int a_note_num)
{
    register int f_i = 0;
    long oldest_tick = LONG_MAX;
    int oldest_tick_voice = -1;

    while(f_i < (data->count))
    {
        if(a_note_num < 0 || a_note_num == data->voices[f_i].note)
        {
            if (data->voices[f_i].on < oldest_tick &&
                data->voices[f_i].on > -1)
            {
                if(!a_running ||
                (data->voices[f_i].n_state != note_state_off))
                {
                    oldest_tick = data->voices[f_i].on;
                    oldest_tick_voice = f_i;
                }
            }
        }

        ++f_i;
    }

    assert(oldest_tick_voice != -1);
    return oldest_tick_voice;
}

/* int i_pick_voice(
 * t_voc_voices *data,
 * int a_current_note)
 *
 */
int i_pick_voice(t_voc_voices *data, int a_current_note,
        long a_current_sample, long a_tick)
{
    register int f_i;

    if(data->poly_mode == 2)
    {
        data->voices[0].on = a_current_sample + a_tick;
        data->voices[0].off = -1;
        data->voices[0].note = a_current_note;
        data->voices[0].n_state = note_state_running;
        return 0;
    }
    else if(data->poly_mode == 3)
    {
        f_i = 0;

        while(f_i < data->count)
        {
            if(data->voices[f_i].n_state == note_state_running ||
                data->voices[f_i].n_state == note_state_releasing)
            {
                data->voices[f_i].n_state = note_state_killed;
                data->voices[f_i].off = a_current_sample + a_tick;
            }

            ++f_i;
        }

        f_i = 0;

        while (f_i < (data->count))
        {
            if (data->voices[f_i].n_state == note_state_off)
            {
                data->voices[f_i].note = a_current_note;
                data->voices[f_i].n_state = note_state_running;
                data->voices[f_i].on = a_current_sample + a_tick;

                return f_i;
            }

            ++f_i;
        }

        data->voices[0].note = a_current_note;
        data->voices[0].n_state = note_state_running;
        data->voices[0].on = a_current_sample + a_tick;
        return 0;
    }


    f_i = 0;
    /* Look for a duplicate note */
    int f_note_count = 0;
    int f_active_count = 0;

    while(f_i < (data->count))
    {
	//if ((data->voices[f_i].note == a_current_note) &&
        //(data->voices[f_i].n_state == note_state_running))
        if(data->voices[f_i].note == a_current_note)
        {
            if((data->voices[f_i].n_state == note_state_releasing)
                    ||
            (data->voices[f_i].n_state == note_state_running))
            {
                data->voices[f_i].n_state = note_state_killed;
                data->voices[f_i].off = a_current_sample;
                ++f_note_count;
            }
            else if(data->voices[f_i].n_state ==
                    note_state_killed)
            {
                ++f_note_count;
            }
            //do not allow more than 2 voices for any note, at any time...
            if(f_note_count > 2)
            {
                int f_steal_voice =
                    i_get_oldest_voice(data, 1, a_current_note);
                data->voices[f_steal_voice].on = a_current_sample + a_tick;
                data->voices[f_steal_voice].note = a_current_note;
                data->voices[f_steal_voice].off = -1;
                data->voices[f_steal_voice].n_state = note_state_running;
                return f_steal_voice;
            }
        }
        ++f_i;
    }

    f_i = 0;
    /* Look for an inactive voice */
    while (f_i < (data->count))
    {
	if (data->voices[f_i].n_state == note_state_off)
        {
            data->voices[f_i].note = a_current_note;
            data->voices[f_i].n_state = note_state_running;
            data->voices[f_i].on = a_current_sample + a_tick;

            return f_i;
	}
        else
        {
            ++f_active_count;

            if(f_active_count >= data->thresh)
            {
                int f_voice_to_kill = i_get_oldest_voice(data, 1, -1);
                data->voices[f_voice_to_kill].n_state = note_state_killed;
                data->voices[f_voice_to_kill].off = a_current_sample;
                --f_active_count;
            }
        }

        ++f_i;
    }

    int oldest_tick_voice = i_get_oldest_voice(data, 0, -1);

    data->voices[oldest_tick_voice].note = a_current_note;
    data->voices[oldest_tick_voice].on = a_current_sample + a_tick;
    data->voices[oldest_tick_voice].n_state = note_state_running;
    data->voices[oldest_tick_voice].off = -1;

    return oldest_tick_voice;
}

/* void v_voc_note_off(t_voc_voices * a_voc, int a_note,
 * long a_current_sample, long a_tick)
 */
void v_voc_note_off(t_voc_voices * a_voc, int a_note,
        long a_current_sample, long a_tick)
{
    if(a_voc->poly_mode == 2)
    {
        //otherwise it's from an old note and should be ignored
        if(a_note == a_voc->voices[0].note)
        {
            a_voc->voices[0].n_state = note_state_releasing;
            a_voc->voices[0].off = a_current_sample + a_tick;
        }
    }
    else
    {
        register int f_i = 0;

        while(f_i < (a_voc->count))
        {
            if(((a_voc->voices[f_i].note) == a_note) &&
               ((a_voc->voices[f_i].n_state) == note_state_running))
            {
                a_voc->voices[f_i].n_state = note_state_releasing;
                a_voc->voices[f_i].off = a_current_sample + a_tick;
            }
            ++f_i;
        }
    }
}

#endif	/* VOICE_H */

