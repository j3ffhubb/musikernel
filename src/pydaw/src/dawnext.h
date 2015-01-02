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


#ifndef DAWNEXT_H
#define	DAWNEXT_H

#define DN_CONFIGURE_KEY_SS "ss"
#define DN_CONFIGURE_KEY_OS "os"
#define DN_CONFIGURE_KEY_SI "si"
#define DN_CONFIGURE_KEY_SR "sr"
#define DN_CONFIGURE_KEY_SAVE_ATM "sa"
#define DN_CONFIGURE_KEY_DN_PLAYBACK "enp"
#define DN_CONFIGURE_KEY_LOOP "loop"
#define DN_CONFIGURE_KEY_TEMPO "tempo"
#define DN_CONFIGURE_KEY_SOLO "solo"
#define DN_CONFIGURE_KEY_MUTE "mute"
#define DN_CONFIGURE_KEY_SET_OVERDUB_MODE "od"
#define DN_CONFIGURE_KEY_PANIC "panic"
//Update a single control for a per-audio-item-fx
#define DN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX "paif"
#define DN_CONFIGURE_KEY_GLUE_AUDIO_ITEMS "ga"
#define DN_CONFIGURE_KEY_MIDI_DEVICE "md"
#define DN_CONFIGURE_KEY_SET_POS "pos"
#define DN_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define DN_CONFIGURE_KEY_UPDATE_SEND "ts"

#define DN_LOOP_MODE_OFF 0
#define DN_LOOP_MODE_REGION 1

#define DN_MAX_ITEM_COUNT 5000
#define DN_MAX_REGION_COUNT 300
#define DN_MAX_EVENTS_PER_ITEM_COUNT 1024

#define DN_TRACK_COUNT 32

#define DN_MAX_REGION_SIZE 64


#include <string.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "pydaw_files.h"
#include "pydaw_plugin_wrapper.h"
#include <sys/stat.h>
#include <sched.h>
#include <unistd.h>
#include <time.h>
#include "../libmodsynth/lib/amp.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "../libmodsynth/lib/peak_meter.h"
#include "../libmodsynth/modules/multifx/multifx3knob.h"
#include "../libmodsynth/modules/modulation/ramp_env.h"
#include "pydaw_audio_tracks.h"
#include "pydaw_audio_inputs.h"
#include "pydaw_audio_util.h"
#include <lo/lo.h>
#include "musikernel.h"


#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    t_pydaw_midi_routing routes[DN_TRACK_COUNT];
}t_dn_midi_routing_list;

typedef struct
{
    t_pydaw_seq_event events[DN_MAX_EVENTS_PER_ITEM_COUNT];
    int event_count;
    t_pydaw_audio_items * audio_items;
    int uid;
}t_dn_item;

typedef struct
{
    int item_uid;
    double start;
    double start_offset;
    double length;
    double end;
}t_dn_item_ref;

typedef struct
{
    int pos;
    int count;
    t_dn_item_ref * refs;
}t_dn_track_seq;

typedef struct
{
    t_dn_track_seq tracks[DN_TRACK_COUNT];
    int uid;
    int bar_length;
    int region_length_bars;
    int region_length_beats;
    float tempo;
}t_dn_region;

typedef struct
{
    double beat;
    int port;
    float val;
    int index;
    int plugin;
}t_dn_atm_point;

typedef struct
{
    t_dn_atm_point * points;
    int point_count;
    char padding[CACHE_LINE_SIZE - sizeof(int) - sizeof(void*)];
}t_dn_atm_plugin;

typedef struct
{
    t_dn_atm_plugin plugins[MAX_PLUGIN_POOL_COUNT];
}t_dn_atm_region;

typedef struct
{
    t_dn_region * regions[DN_MAX_REGION_COUNT];
    t_dn_atm_region * regions_atm;
}t_dn_song;

typedef struct
{
    int track_pool_sorted[MAX_WORKER_THREADS][DN_TRACK_COUNT]
        __attribute__((aligned(CACHE_LINE_SIZE)));
    t_pytrack_routing routes[DN_TRACK_COUNT][MAX_ROUTING_COUNT]
        __attribute__((aligned(CACHE_LINE_SIZE)));
    int bus_count[DN_TRACK_COUNT];
    int track_pool_sorted_count;
}t_dn_routing_graph;

typedef struct
{
    float ml_sample_period_inc_beats;

    int ml_current_region;
    float ml_current_beat;
    int ml_next_region;
    float ml_next_beat;
    int ml_is_looping;
    char padding[CACHE_LINE_SIZE - (7 * sizeof(float)) - (4 * sizeof(int))];
}t_dn_thread_storage;

typedef struct
{
    t_dn_thread_storage ts[MAX_WORKER_THREADS];
    t_dn_song * en_song;
    t_pytrack * track_pool[DN_TRACK_COUNT];
    t_dn_routing_graph * routing_graph;
    int loop_mode;  //0 == Off, 1 == Bar, 2 == Region
    int overdub_mode;  //0 == Off, 1 == On

    /*the increment per-period to iterate through 1 bar,
     * as determined by sample rate and tempo*/
    float playback_inc;
    int current_region; //the current region

    long current_sample;
    //The number of samples per beat, for calculating length
    float samples_per_beat;

    t_dn_item * item_pool[DN_MAX_ITEM_COUNT];

    int is_soloed;

    /*used to prevent new audio items from playing while
     * the existing are being faded out.*/
    int suppress_new_audio_items;

    int audio_glue_indexes[PYDAW_MAX_AUDIO_ITEM_COUNT];

    long f_next_current_sample;
    t_dn_midi_routing_list midi_routing;

    char * project_folder;
    char * item_folder;
    char * region_folder;
    char * tracks_folder;
}t_dawnext;


void g_dn_song_get(t_dawnext*, int);
t_dn_routing_graph * g_dn_routing_graph_get(t_dawnext *);
void v_dn_routing_graph_free(t_dn_routing_graph*);
t_dn_region * g_dn_region_get(t_dawnext*, const int);
t_dn_atm_region * g_dn_atm_region_get(t_dawnext*);
void v_dn_atm_region_free(t_dn_atm_region*);
void g_dn_item_get(t_dawnext*, int);

t_dawnext * g_dawnext_get();
int i_dn_get_region_index_from_name(t_dawnext *, int);
void v_dn_set_tempo(t_dawnext*,float);
void v_dn_set_is_soloed(t_dawnext * self);
void v_dn_set_loop_mode(t_dawnext * self, int a_mode);
void v_dn_set_playback_cursor(t_dawnext*, double);
int i_dn_song_index_from_region_uid(t_dawnext*, int);
void v_dn_update_track_send(t_dawnext * self, int a_lock);
void v_dn_process_external_midi(t_dawnext * pydaw_data,
        t_pytrack * a_track, int sample_count, int a_thread_num,
        t_dn_thread_storage * a_ts);
void v_dn_offline_render(t_dawnext*, double, double,
    char*, int, int, t_dn_item_ref*);
void v_dn_audio_items_run(t_dawnext*, t_dn_item_ref*,
    int, float**, float**, int, int, int*, t_dn_thread_storage*);

void v_dn_paif_set_control(t_dawnext*, int, int, int, float);

void v_dn_song_free(t_dn_song *);
void v_dn_process_note_offs(t_dawnext * self, int f_i);
void v_dn_process_midi(
    t_dawnext *, t_dn_item_ref*, int, int, int, t_dn_thread_storage*);
void v_dn_zero_all_buffers(t_dawnext * self);
void v_dn_panic(t_dawnext * self);

void v_dn_process_atm(t_dawnext * self, int f_track_num,
    int f_index, int sample_count, int a_playback_mode,
    t_dn_thread_storage * a_ts);

void v_dn_set_midi_device(int, int, int);
void v_dn_set_midi_devices();

void g_dn_midi_routing_list_init(t_dn_midi_routing_list*);

#ifdef	__cplusplus
}
#endif

t_dawnext * dawnext;

void g_dn_midi_routing_list_init(t_dn_midi_routing_list * self)
{
    int f_i;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        self->routes[f_i].on = 0;
        self->routes[f_i].output_track = -1;
    }
}

void g_dn_instantiate()
{
    dawnext = g_dawnext_get();
}

void v_dn_reset_audio_item_read_heads(t_dawnext * self,
        t_pydaw_audio_items * f_audio_items, double a_start_beat)
{
    if(a_start_beat == 0.0f)
    {
        return;  //no need to run because the audio loop will reset it all
    }

    if(!f_audio_items)
    {
        return;
    }

    register int f_i;
    int f_i2;
    float f_sr = musikernel->thread_storage[0].sample_rate;
    t_pydaw_audio_item * f_audio_item;
    float f_tempo = self->en_song->regions[0]->tempo;

    for(f_i = 0; f_i < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i)
    {
        if(f_audio_items->items[f_i])
        {
            f_audio_item = f_audio_items->items[f_i];
            double f_start_beat = f_audio_item->start_beat;

            double f_end_beat =
                f_start_beat + f_pydaw_samples_to_beat_count(
                    (f_audio_item->sample_end_offset -
                     f_audio_item->sample_start_offset),
                    f_tempo, f_sr);

            if((a_start_beat > f_start_beat) && (a_start_beat < f_end_beat))
            {
                double f_beats_offset = (a_start_beat - f_start_beat);
                int f_sample_start = i_beat_count_to_samples(
                        f_beats_offset, f_tempo, f_sr);

                for(f_i2 = 0; f_i2 < MK_AUDIO_ITEM_SEND_COUNT; ++f_i2)
                {
                    v_ifh_retrigger(
                        &f_audio_item->sample_read_heads[f_i2], f_sample_start);

                    v_adsr_retrigger(&f_audio_item->adsrs[f_i2]);
                }
            }
        }
    }
}

/* void v_dn_zero_all_buffers(t_pydaw_data * self)
 */
void v_dn_zero_all_buffers(t_dawnext * self)
{
    int f_i;
    float ** f_buff;
    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        f_buff = self->track_pool[f_i]->buffers;
        v_pydaw_zero_buffer(f_buff, FRAMES_PER_BUFFER);
    }
}

/* void v_dn_panic(t_pydaw_data * self)
 *
 */
void v_dn_panic(t_dawnext * self)
{
    register int f_i = 0;
    register int f_i2 = 0;
    t_pytrack * f_track;
    t_pydaw_plugin * f_plugin;

    while(f_i < DN_TRACK_COUNT)
    {
        f_track = self->track_pool[f_i];

        f_i2 = 0;
        while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
        {
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->panic)
            {
                f_plugin->descriptor->panic(f_plugin->PYFX_handle);
            }
            ++f_i2;
        }

        ++f_i;
    }

    v_dn_zero_all_buffers(self);
}


void v_dn_song_free(t_dn_song * a_dn_song)
{
    int f_i = 0;
    while(f_i < DN_MAX_REGION_COUNT)
    {
        if(a_dn_song->regions[f_i])
        {
            free(a_dn_song->regions[f_i]);
        }

        ++f_i;
    }
}

void v_dn_paif_set_control(t_dawnext * self,
        int a_item_index, int a_audio_item_index, int a_port, float a_val)
{
    int f_effect_index = a_port / 4;
    int f_control_index = a_port % 4;

    t_pydaw_audio_item * f_audio_item = self->item_pool[
        a_item_index]->audio_items->items[a_audio_item_index];

    t_paif * f_region = f_audio_item->paif;
    t_per_audio_item_fx * f_item;

    float f_sr = musikernel->thread_storage[0].sample_rate;

    if(!f_region)
    {
        f_region = g_paif8_get();
        pthread_spin_lock(&musikernel->main_lock);
        f_audio_item->paif = f_region;
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(!f_region->loaded)
    {
        t_per_audio_item_fx * f_items[8];
        int f_i = 0;
        while(f_i < 8)
        {
            f_items[f_i] = g_paif_get(f_sr);
            ++f_i;
        }
        pthread_spin_lock(&musikernel->main_lock);
        f_i = 0;
        while(f_i < 8)
        {
            f_region->items[f_i] = f_items[f_i];
            ++f_i;
        }
        f_region->loaded = 1;
        pthread_spin_unlock(&musikernel->main_lock);
    }

    f_item = f_region->items[f_effect_index];

    pthread_spin_lock(&musikernel->main_lock);

    if(f_control_index == 3)
    {
        int f_fx_index = (int)a_val;
        f_item->fx_type = f_fx_index;
        f_item->func_ptr = g_mf3_get_function_pointer(f_fx_index);

        v_mf3_set(f_item->mf3, f_item->a_knobs[0],
            f_item->a_knobs[1], f_item->a_knobs[2]);
    }
    else
    {
        f_region->items[
            f_effect_index]->a_knobs[f_control_index] = a_val;

        v_mf3_set(f_item->mf3, f_item->a_knobs[0],
            f_item->a_knobs[1], f_item->a_knobs[2]);
    }

    pthread_spin_unlock(&musikernel->main_lock);

}

void v_dn_osc_send(t_osc_send_data * a_buffers)
{
    int f_i;
    t_pkm_peak_meter * f_pkm;

    a_buffers->f_tmp1[0] = '\0';
    a_buffers->f_tmp2[0] = '\0';

    f_pkm = dawnext->track_pool[0]->peak_meter;
    sprintf(a_buffers->f_tmp2, "%i:%f:%f", 0, f_pkm->value[0], f_pkm->value[1]);
    v_pkm_reset(f_pkm);

    for(f_i = 1; f_i < DN_TRACK_COUNT; ++f_i)
    {
        f_pkm = dawnext->track_pool[f_i]->peak_meter;
        if(!f_pkm->dirty)  //has ran since last v_pkm_reset())
        {
            sprintf(a_buffers->f_tmp1, "|%i:%f:%f",
                f_i, f_pkm->value[0], f_pkm->value[1]);
            v_pkm_reset(f_pkm);
            strcat(a_buffers->f_tmp2, a_buffers->f_tmp1);
        }
    }

    v_queue_osc_message("peak", a_buffers->f_tmp2);

    a_buffers->f_tmp1[0] = '\0';
    a_buffers->f_tmp2[0] = '\0';

    if(musikernel->playback_mode > 0 && !musikernel->is_offline_rendering)
    {
        sprintf(a_buffers->f_msg, "%f",
            dawnext->ts[0].ml_current_beat);
        v_queue_osc_message("cur", a_buffers->f_msg);
    }

    if(musikernel->osc_queue_index > 0)
    {
        f_i = 0;

        while(f_i < musikernel->osc_queue_index)
        {
            strcpy(a_buffers->osc_queue_keys[f_i],
                musikernel->osc_queue_keys[f_i]);
            strcpy(a_buffers->osc_queue_vals[f_i],
                musikernel->osc_queue_vals[f_i]);
            ++f_i;
        }

        pthread_spin_lock(&musikernel->main_lock);

        //Now grab any that may have been written since the previous copy

        while(f_i < musikernel->osc_queue_index)
        {
            strcpy(a_buffers->osc_queue_keys[f_i],
                musikernel->osc_queue_keys[f_i]);
            strcpy(a_buffers->osc_queue_vals[f_i],
                musikernel->osc_queue_vals[f_i]);
            ++f_i;
        }

        int f_index = musikernel->osc_queue_index;
        musikernel->osc_queue_index = 0;

        pthread_spin_unlock(&musikernel->main_lock);

        f_i = 0;

        a_buffers->f_tmp1[0] = '\0';

        while(f_i < f_index)
        {
            sprintf(a_buffers->f_tmp2, "%s|%s\n",
                a_buffers->osc_queue_keys[f_i],
                a_buffers->osc_queue_vals[f_i]);
            strcat(a_buffers->f_tmp1, a_buffers->f_tmp2);
            ++f_i;
        }

        if(!musikernel->is_offline_rendering)
        {
            lo_send(musikernel->uiTarget,
                "musikernel/dawnext", "s", a_buffers->f_tmp1);
        }
    }
}


void v_dn_sum_track_outputs(t_dawnext * self, t_pytrack * a_track,
        int a_sample_count, int a_playback_mode, t_dn_thread_storage * a_ts)
{
    int f_bus_num;
    register int f_i2;
    t_pytrack * f_bus;
    t_pytrack_routing * f_route;
    t_pydaw_plugin * f_plugin = 0;
    float ** f_buff;
    float ** f_track_buff = a_track->buffers;

    if((dawnext->routing_graph->bus_count[a_track->track_num])
        ||
        ((!a_track->mute) && (!self->is_soloed))
        ||
        ((self->is_soloed) && (a_track->solo)))
    {
        if(a_track->fade_state == FADE_STATE_FADED)
        {
            a_track->fade_state = FADE_STATE_RETURNING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_FADING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_RETURNING;
        }
    }
    else
    {
        if(a_track->fade_state == FADE_STATE_OFF)
        {
            a_track->fade_state = FADE_STATE_FADING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_RETURNING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_FADING;
        }
    }

    f_i2 = 0;

    if(a_track->fade_state == FADE_STATE_OFF)
    {

    }
    else if(a_track->fade_state == FADE_STATE_FADING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);

            f_track_buff[0][f_i2] *= (1.0f - a_track->fade_env.output);
            f_track_buff[1][f_i2] *= (1.0f - a_track->fade_env.output);
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_FADED;
        }
    }
    else if(a_track->fade_state == FADE_STATE_RETURNING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);
            f_track_buff[0][f_i2] *= a_track->fade_env.output;
            f_track_buff[1][f_i2] *= a_track->fade_env.output;
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_OFF;
        }
    }


    int f_i3;

    for(f_i3 = 0; f_i3 < MAX_ROUTING_COUNT; ++f_i3)
    {
        f_route = &self->routing_graph->routes[a_track->track_num][f_i3];

        if(!f_route->active)
        {
            continue;
        }

        f_bus_num = f_route->output;

        if(f_bus_num < 0)
        {
            continue;
        }

        int f_plugin_index = MAX_PLUGIN_COUNT + f_i3;

        if(a_track->plugins[f_plugin_index])
        {
            f_plugin = a_track->plugins[f_plugin_index];
        }
        else
        {
            f_plugin = 0;
        }

        f_bus = self->track_pool[f_bus_num];

        if(f_route->sidechain)
        {
            f_buff = f_bus->sc_buffers;
            f_bus->sc_buffers_dirty = 1;
        }
        else
        {
            f_buff = f_bus->buffers;
        }

        if(a_track->fade_state != FADE_STATE_FADED)
        {
            if(f_plugin && f_plugin->power)
            {
                v_dn_process_atm(self, a_track->track_num,
                    f_plugin_index, a_sample_count, a_playback_mode, a_ts);

                pthread_spin_lock(&f_bus->lock);

                f_plugin->descriptor->run_mixing(
                    f_plugin->PYFX_handle, a_sample_count,
                    f_buff, 2, a_track->event_buffer,
                    a_track->period_event_index,
                    f_plugin->atm_buffer, f_plugin->atm_count,
                    a_track->extern_midi, *a_track->extern_midi_count);
            }
            else
            {
                pthread_spin_lock(&f_bus->lock);

                v_buffer_mix(a_sample_count, f_track_buff, f_buff);
            }
        }
        else
        {
            pthread_spin_lock(&f_bus->lock);
        }

        --f_bus->bus_counter;
        pthread_spin_unlock(&f_bus->lock);
    }
}

void v_dn_wait_for_bus(t_pytrack * a_track)
{
    int f_bus_count = dawnext->routing_graph->bus_count[a_track->track_num];
    int f_i;

    if(a_track->track_num && f_bus_count)
    {
        for(f_i = 0; f_i < 100000000; ++f_i)
        {
            pthread_spin_lock(&a_track->lock);

            if(a_track->bus_counter <= 0)
            {
                pthread_spin_unlock(&a_track->lock);
                break;
            }

            pthread_spin_unlock(&a_track->lock);
        }

        if(f_i == 100000000)
        {
            printf("Detected deadlock waiting for bus %i\n",
                a_track->track_num);
        }

        if(a_track->bus_counter < 0)
        {
            printf("Bus %i had bus_counter < 0: %i\n",
                a_track->track_num, a_track->bus_counter);
        }
    }
}

void v_dn_process_track(t_dawnext * self, int a_global_track_num,
        int a_thread_num, int a_sample_count, int a_playback_mode,
        t_dn_thread_storage * a_ts)
{
    int f_i;
    t_pytrack * f_track = self->track_pool[a_global_track_num];
    t_dn_track_seq * f_seq =
        &self->en_song->regions[0]->tracks[a_global_track_num];
    t_dn_item_ref * f_item_ref = NULL;
    t_pydaw_plugin * f_plugin;

    while(1)
    {
        if(f_seq->pos >= f_seq->count)
        {
            break;
        }

        if(f_seq->refs[f_seq->pos].end > a_ts->ml_current_beat)
        {
            f_item_ref = &f_seq->refs[f_seq->pos];
            break;
        }
        else if(f_seq->refs[f_seq->pos].end < a_ts->ml_current_beat)
        {
            ++f_seq->pos;
        }
        else
        {
            break;
        }
    }

    if(a_playback_mode > 0  && f_item_ref)
    {
        v_dn_process_midi(self, f_item_ref, a_global_track_num,
            a_sample_count, a_playback_mode, a_ts);
    }
    else
    {
        f_track->period_event_index = 0;
    }

    v_dn_process_external_midi(self, f_track, a_sample_count,
        a_thread_num, a_ts);

    v_dn_process_note_offs(self, a_global_track_num);

    v_dn_wait_for_bus(f_track);

    if(f_item_ref)
    {
        v_dn_audio_items_run(self, f_item_ref, a_sample_count,
            f_track->buffers, f_track->sc_buffers, a_global_track_num, 0,
            &f_track->sc_buffers_dirty, a_ts);
    }
    f_i = 0;

    while(f_i < MAX_PLUGIN_COUNT)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin && f_plugin->power)
        {
            v_dn_process_atm(self, a_global_track_num,
                f_i, a_sample_count, a_playback_mode, a_ts);
            f_plugin->descriptor->run_replacing(
                f_plugin->PYFX_handle, a_sample_count,
                f_track->event_buffer, f_track->period_event_index,
                f_plugin->atm_buffer, f_plugin->atm_count,
                f_track->extern_midi, *f_track->extern_midi_count);
        }
        ++f_i;
    }

    if(a_global_track_num)
    {
        v_dn_sum_track_outputs(self, f_track,
            a_sample_count, a_playback_mode, a_ts);
    }

    v_pkm_run(f_track->peak_meter, f_track->buffers[0],
        f_track->buffers[1], a_sample_count);

    if(a_global_track_num)
    {
        v_pydaw_zero_buffer(f_track->buffers, a_sample_count);
    }

    if(f_track->sc_buffers_dirty)
    {
        f_track->sc_buffers_dirty = 0;
        v_pydaw_zero_buffer(f_track->sc_buffers, a_sample_count);
    }
}

inline void v_dn_process(t_pydaw_thread_args * f_args)
{
    t_pytrack * f_track;
    int f_track_index;
    t_dawnext * self = dawnext;
    int f_i = f_args->thread_num;
    int f_sorted_count = self->routing_graph->track_pool_sorted_count;
    int * f_sorted = self->routing_graph->track_pool_sorted[f_args->thread_num];
    int f_sample_count = musikernel->sample_count;
    int f_playback_mode = musikernel->playback_mode;

    t_dn_thread_storage * f_ts = &dawnext->ts[f_args->thread_num];

    if(f_args->thread_num > 0)
    {
        memcpy(f_ts, &dawnext->ts[0], sizeof(t_dn_thread_storage));
    }

    while(f_i < f_sorted_count)
    {
        f_track_index = f_sorted[f_i];
        f_track = self->track_pool[f_track_index];

        if(f_track->status != STATUS_NOT_PROCESSED)
        {
            ++f_i;
            continue;
        }

        pthread_spin_lock(&f_track->lock);

        if(f_track->status == STATUS_NOT_PROCESSED)
        {
            f_track->status = STATUS_PROCESSING;
        }
        else
        {
            pthread_spin_unlock(&f_track->lock);
            ++f_i;
            continue;
        }

        pthread_spin_unlock(&f_track->lock);

        v_dn_process_track(self, f_track->track_num, f_args->thread_num,
            f_sample_count, f_playback_mode, f_ts);

        f_track->status = STATUS_PROCESSED;

        ++f_i;
    }
}


inline void v_dn_process_atm(
    t_dawnext * self, int f_track_num, int f_index, int sample_count,
    int a_playback_mode, t_dn_thread_storage * a_ts)
{
    t_pytrack * f_track = self->track_pool[f_track_num];
    t_pydaw_plugin * f_plugin = f_track->plugins[f_index];
    float f_track_current_period_beats = a_ts->ml_current_beat;
    float f_track_next_period_beats = a_ts->ml_next_beat;
    float f_track_beats_offset = 0.0f;
    int f_pool_index = f_plugin->pool_uid;

    f_plugin->atm_count = 0;

    if((!self->overdub_mode) && (a_playback_mode == 2) &&
        (f_track->extern_midi))
    {
        return;
    }

    while(1)
    {
        if(self->en_song->regions_atm &&
            self->en_song->regions_atm->plugins[f_pool_index].point_count)
        {
            t_dn_atm_plugin * f_current_item =
                &self->en_song->regions_atm->plugins[f_pool_index];

            if((f_plugin->atm_pos) >= (f_current_item->point_count))
            {
                break;
            }

            t_dn_atm_point * f_point =
                &f_current_item->points[f_plugin->atm_pos];

            if(f_point->beat < f_track_current_period_beats)
            {
                ++f_plugin->atm_pos;
                continue;
            }

            if((f_point->beat >= f_track_current_period_beats) &&
                (f_point->beat < f_track_next_period_beats))
            {
                t_pydaw_seq_event * f_buff_ev =
                    &f_plugin->atm_buffer[f_plugin->atm_count];

                int f_note_sample_offset = 0;
                float f_note_start_diff =
                    ((f_point->beat) - f_track_current_period_beats) +
                    f_track_beats_offset;
                float f_note_start_frac =
                    f_note_start_diff / a_ts->ml_sample_period_inc_beats;
                f_note_sample_offset =
                    (int)(f_note_start_frac * (float)sample_count);

                if(f_plugin->uid == f_point->plugin)
                {
                    float f_val = f_atm_to_ctrl_val(
                        f_plugin->descriptor, f_point->port, f_point->val);
                    v_pydaw_ev_clear(f_buff_ev);
                    v_pydaw_ev_set_atm(f_buff_ev, f_point->port, f_val);
                    f_buff_ev->tick = f_note_sample_offset;
                    v_pydaw_set_control_from_atm(
                        f_buff_ev, f_plugin->pool_uid, f_track);
                    ++f_plugin->atm_count;
                }
                ++f_plugin->atm_pos;
            }
            else
            {
                break;
            }
        }
        else
        {
            break;
        }
    }
}

void v_dn_process_midi(t_dawnext * self, t_dn_item_ref * a_item_ref,
        int f_i, int sample_count, int a_playback_mode,
        t_dn_thread_storage * a_ts)
{
    t_dn_item * f_current_item;
    double f_adjusted_start;
    t_pytrack * f_track = self->track_pool[f_i];
    f_track->period_event_index = 0;

    float f_track_current_period_beats = (a_ts->ml_current_beat);
    float f_track_next_period_beats = (a_ts->ml_next_beat);
    float f_track_beats_offset = 0.0f;

    if((!self->overdub_mode) && (a_playback_mode == 2) &&
        (f_track->extern_midi))
    {

    }
    else
    {
        while(1)
        {
            f_current_item = self->item_pool[a_item_ref->item_uid];

            if((f_track->item_event_index) >= (f_current_item->event_count))
            {
                break;
            }

            t_pydaw_seq_event * f_event =
                &f_current_item->events[f_track->item_event_index];

            f_adjusted_start = f_event->start + a_item_ref->start;

            if((f_adjusted_start >= f_track_current_period_beats) &&
                (f_adjusted_start < f_track_next_period_beats))
            {
                if(f_event->type == PYDAW_EVENT_NOTEON)
                {
                    int f_note_sample_offset = 0;
                    float f_note_start_diff =
                        f_adjusted_start - f_track_current_period_beats +
                        f_track_beats_offset;
                    float f_note_start_frac = f_note_start_diff /
                            (a_ts->ml_sample_period_inc_beats);
                    f_note_sample_offset =  (int)(f_note_start_frac *
                            ((float)sample_count));

                    if(f_track->note_offs[f_event->note]
                        >= (self->current_sample))
                    {
                        t_pydaw_seq_event * f_buff_ev;

                        /*There's already a note_off scheduled ahead of
                         * this one, process it immediately to avoid
                         * hung notes*/
                        f_buff_ev = &f_track->event_buffer[
                            f_track->period_event_index];
                        v_pydaw_ev_clear(f_buff_ev);

                        v_pydaw_ev_set_noteoff(f_buff_ev, 0,
                                (f_event->note), 0);
                        f_buff_ev->tick = f_note_sample_offset;

                        ++f_track->period_event_index;
                    }

                    t_pydaw_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    v_pydaw_ev_clear(f_buff_ev);

                    v_pydaw_ev_set_noteon(f_buff_ev, 0,
                            f_event->note, f_event->velocity);

                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;

                    f_track->note_offs[(f_event->note)] =
                        (self->current_sample) + ((int)(f_event->length *
                        self->samples_per_beat));
                }
                else if(f_event->type == PYDAW_EVENT_CONTROLLER)
                {
                    int controller = f_event->param;

                    t_pydaw_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    int f_note_sample_offset = 0;

                    float f_note_start_diff =
                        ((f_adjusted_start) - f_track_current_period_beats) +
                        f_track_beats_offset;
                    float f_note_start_frac = f_note_start_diff /
                        a_ts->ml_sample_period_inc_beats;
                    f_note_sample_offset =
                        (int)(f_note_start_frac * ((float)sample_count));

                    v_pydaw_ev_clear(f_buff_ev);

                    v_pydaw_ev_set_controller(
                        f_buff_ev, 0, controller, f_event->value);

                    v_pydaw_set_control_from_cc(f_buff_ev, f_track);

                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;
                }
                else if(f_event->type == PYDAW_EVENT_PITCHBEND)
                {
                    int f_note_sample_offset = 0;
                    float f_note_start_diff = ((f_adjusted_start) -
                    f_track_current_period_beats) + f_track_beats_offset;
                    float f_note_start_frac = f_note_start_diff /
                        a_ts->ml_sample_period_inc_beats;
                    f_note_sample_offset =  (int)(f_note_start_frac *
                        ((float)sample_count));

                    t_pydaw_seq_event * f_buff_ev =
                        &f_track->event_buffer[f_track->period_event_index];

                    v_pydaw_ev_clear(f_buff_ev);
                    v_pydaw_ev_set_pitchbend(f_buff_ev, 0, f_event->value);
                    f_buff_ev->tick = f_note_sample_offset;

                    ++f_track->period_event_index;
                }

                ++f_track->item_event_index;
            }
            else
            {
                break;
            }
        }
    }
}

void v_dn_process_note_offs(t_dawnext * self, int f_i)
{
    t_pytrack * f_track = self->track_pool[f_i];
    long f_current_sample = self->current_sample;
    long f_next_current_sample = self->f_next_current_sample;

    register int f_i2 = 0;
    long f_note_off;

    while(f_i2 < PYDAW_MIDI_NOTE_COUNT)
    {
        f_note_off = f_track->note_offs[f_i2];
        if(f_note_off >=  f_current_sample &&
           f_note_off < f_next_current_sample)
        {
            t_pydaw_seq_event * f_event =
                &f_track->event_buffer[f_track->period_event_index];
            v_pydaw_ev_clear(f_event);

            v_pydaw_ev_set_noteoff(f_event, 0, f_i2, 0);
            f_event->tick = f_note_off - f_current_sample;
            ++f_track->period_event_index;
            f_track->note_offs[f_i2] = -1;
        }
        ++f_i2;
    }
}

void v_dn_process_external_midi(t_dawnext * self,
        t_pytrack * a_track, int sample_count, int a_thread_num,
        t_dn_thread_storage * a_ts)
{
    if(!a_track->midi_device)
    {
        return;
    }

    float f_sample_rate = musikernel->thread_storage[a_thread_num].sample_rate;
    int f_playback_mode = musikernel->playback_mode;
    int f_midi_learn = musikernel->midi_learn;
    float f_tempo = self->en_song->regions[0]->tempo;

    midiDeviceRead(a_track->midi_device, f_sample_rate, sample_count);

    int f_extern_midi_count = *a_track->extern_midi_count;
    t_pydaw_seq_event * events = a_track->extern_midi;

    assert(f_extern_midi_count < 200);

    register int f_i2 = 0;

    char * f_osc_msg = a_track->osc_cursor_message;

    while(f_i2 < f_extern_midi_count)
    {
        if(events[f_i2].tick >= sample_count)
        {
            //Otherwise the event will be missed
            events[f_i2].tick = sample_count - 1;
        }

        if(events[f_i2].type == PYDAW_EVENT_NOTEON)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_beat +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "on|%f|%i|%i|%i|%ld",
                    f_beat, a_track->track_num, events[f_i2].note,
                    events[f_i2].velocity,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sprintf(f_osc_msg, "1|%i", events[f_i2].note);
            v_queue_osc_message("ne", f_osc_msg);

        }
        else if(events[f_i2].type == PYDAW_EVENT_NOTEOFF)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_beat +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "off|%f|%i|%i|%ld",
                    f_beat, a_track->track_num, events[f_i2].note,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sprintf(f_osc_msg, "0|%i", events[f_i2].note);
            v_queue_osc_message("ne", f_osc_msg);
        }
        else if(events[f_i2].type == PYDAW_EVENT_PITCHBEND)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_beat +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "pb|%f|%i|%f|%ld",
                    f_beat, a_track->track_num, events[f_i2].value,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }
        }
        else if(events[f_i2].type == PYDAW_EVENT_CONTROLLER)
        {
            int controller = events[f_i2].param;

            if(f_midi_learn)
            {
                musikernel->midi_learn = 0;
                f_midi_learn = 0;
                sprintf(f_osc_msg, "%i", controller);
                v_queue_osc_message("ml", f_osc_msg);
            }

            /*float f_start =
                ((self->playback_cursor) +
                ((((float)(events[f_i2].tick)) / ((float)sample_count))
                * (self->playback_inc))) * 4.0f;*/
            v_pydaw_set_control_from_cc(&events[f_i2], a_track);

            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat =
                    a_ts->ml_current_beat +
                    f_pydaw_samples_to_beat_count(
                        events[f_i2].tick, f_tempo,
                        f_sample_rate);

                sprintf(f_osc_msg,
                    "cc|%f|%i|%i|%f",
                    f_beat,
                    a_track->track_num, controller, events[f_i2].value);
                v_queue_osc_message("mrec", f_osc_msg);
            }
        }
        ++f_i2;
    }
}


inline void v_dn_set_time_params(t_dawnext * self, int sample_count)
{
    self->ts[0].ml_sample_period_inc_beats =
        ((self->playback_inc) * ((float)(sample_count)));
    self->ts[0].ml_current_beat =
        self->ts[0].ml_next_beat;
    self->ts[0].ml_next_beat = self->ts[0].ml_current_beat +
        self->ts[0].ml_sample_period_inc_beats;

    self->ts[0].ml_current_region = (self->current_region);

    self->ts[0].ml_next_region = (self->current_region);

    /*
    if((self->ts[0].ml_next_period_beats) > 4.0f)
    {
        self->ts[0].ml_starting_new_bar = 1;
        self->ts[0].ml_next_beat =
            (self->ts[0].ml_next_period_beats) - 4.0f;

        int f_region_length = 8;
        if(self->en_song->regions[(self->current_region)])
        {
            f_region_length =
                (self->en_song->regions[
                    (self->current_region)]->region_length_bars);
        }

        if(f_region_length == 0)
        {
            f_region_length = 8;
        }

        if((self->ts[0].ml_next_bar) >= f_region_length)
        {
            self->ts[0].ml_next_bar = 0;
            if(self->loop_mode != DN_LOOP_MODE_REGION)
            {
                ++self->ts[0].ml_next_region;
            }
            else
            {
                self->ts[0].ml_is_looping = 1;
            }
        }
    }
    else
    */
    if(1)
    {
        self->ts[0].ml_is_looping = 0;
        self->ts[0].ml_next_region = self->current_region;
    }
}

inline void v_dn_finish_time_params(t_dawnext * self)
{
    /*
    self->playback_cursor = (self->ts[0].ml_next_playback_cursor);

    if((self->playback_cursor) >= 1.0f)
    {
        self->playback_cursor = (self->playback_cursor) - 1.0f;

        if((self->current_bar) >= a_region_length_bars)
        {
            self->current_bar = 0;

            if(self->loop_mode != DN_LOOP_MODE_REGION)
            {
                ++self->current_region;

                if((self->current_region) >= DN_MAX_REGION_COUNT)
                {
                    musikernel->playback_mode = 0;
                    self->current_region = 0;
                }
            }
            else if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = self->ts[0].ml_current_beat;

                sprintf(musikernel->osc_cursor_message, "loop|%i|%i|%f|%ld",
                    f_beat, self->current_sample +
                    i_beat_count_to_samples(4.0 - f_beat, self->tempo,
                        musikernel->thread_storage[0].sample_rate));
                v_queue_osc_message("mrec", musikernel->osc_cursor_message);
            }
        }
    }
    */
}

inline void v_dn_run_engine(int sample_count,
        float **output, float *a_input_buffers)
{
    t_dawnext * self = dawnext;
    //notify the worker threads to wake up
    register int f_i = 1;
    while(f_i < musikernel->worker_thread_count)
    {
        pthread_spin_lock(&musikernel->thread_locks[f_i]);
        pthread_mutex_lock(&musikernel->track_block_mutexes[f_i]);
        pthread_cond_broadcast(&musikernel->track_cond[f_i]);
        pthread_mutex_unlock(&musikernel->track_block_mutexes[f_i]);
        ++f_i;
    }

    long f_next_current_sample = dawnext->current_sample + sample_count;

    musikernel->sample_count = sample_count;
    self->f_next_current_sample = f_next_current_sample;

    if((musikernel->playback_mode) > 0)
    {
        v_dn_set_time_params(self, sample_count);
    }

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        self->track_pool[f_i]->status = STATUS_NOT_PROCESSED;
        self->track_pool[f_i]->bus_counter =
            self->routing_graph->bus_count[f_i];
    }

    //unleash the hounds
    for(f_i = 1; f_i < musikernel->worker_thread_count; ++f_i)
    {
        pthread_spin_unlock(&musikernel->thread_locks[f_i]);
    }

    v_dn_process((t_pydaw_thread_args*)musikernel->main_thread_args);

    t_pytrack * f_master_track = self->track_pool[0];
    float ** f_master_buff = f_master_track->buffers;

    //wait for the other threads to finish
    v_wait_for_threads();

    v_dn_process_track(self, 0, 0, sample_count,
        musikernel->playback_mode, &self->ts[0]);

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = f_master_buff[0][f_i];
        output[1][f_i] = f_master_buff[1][f_i];
    }

    v_pydaw_zero_buffer(f_master_buff, sample_count);

    if((musikernel->playback_mode) > 0)
    {
        v_dn_finish_time_params(self);
    }

    dawnext->current_sample = f_next_current_sample;
}


void v_dn_audio_items_run(t_dawnext * self, t_dn_item_ref * a_item_ref,
    int a_sample_count, float** a_buff, float ** a_sc_buff,
    int a_audio_track_num, int a_is_audio_glue, int * a_sc_dirty,
    t_dn_thread_storage * a_ts)
{
    t_dn_item * f_item = self->item_pool[a_item_ref->item_uid];

    if(!a_is_audio_glue &&
    (!f_item->audio_items->index_counts[0]))
    {
        return;
    }

    int f_playback_mode = musikernel->playback_mode;
    t_per_audio_item_fx * f_paif_item;

    t_pydaw_audio_items * f_region = f_item->audio_items;

    int f_i = 0;
    int f_index_pos = 0;
    int f_send_num = 0;
    float ** f_buff = a_buff;

    while(a_is_audio_glue ||
        f_index_pos < f_region->index_counts[0])
    {
        if(!a_is_audio_glue)
        {
            f_i = f_region->indexes[0][f_index_pos].item_num;
            //f_send_num = f_region->indexes[0][f_index_pos].send_num;
            ++f_index_pos;
        }
        else
        {
            if(f_i >= PYDAW_MAX_AUDIO_ITEM_COUNT)
            {
                break;
            }
        }

        if(f_region->items[f_i] == 0)
        {
            ++f_i;
            continue;
        }

        t_pydaw_audio_item * f_audio_item = f_region->items[f_i];

        if(!a_is_audio_glue && f_audio_item->sidechain[f_send_num])
        {
            f_buff = a_sc_buff;
            *a_sc_dirty = 1;
        }

        if(self->suppress_new_audio_items &&
            ((f_audio_item->adsrs[f_send_num].stage) == ADSR_STAGE_OFF))
        {
            ++f_i;
            continue;
        }

        if(a_is_audio_glue  && !self->audio_glue_indexes[f_i])
        {
            ++f_i;
            continue;
        }

        if(f_playback_mode == PYDAW_PLAYBACK_MODE_OFF &&
            f_audio_item->adsrs[f_send_num].stage < ADSR_STAGE_RELEASE)
        {
            v_adsr_release(&f_audio_item->adsrs[f_send_num]);
        }

        double f_audio_start = f_audio_item->adjusted_start_beat +
            a_item_ref->start;

        if(f_audio_start >= a_ts->ml_next_beat)
        {
            ++f_i;
            continue;
        }

        register int f_i2 = 0;

        if((f_audio_start >= a_ts->ml_current_beat) &&
            (f_audio_start < a_ts->ml_next_beat))
        {
            if(f_audio_item->is_reversed)
            {
                v_ifh_retrigger(
                    &f_audio_item->sample_read_heads[f_send_num],
                    f_audio_item->sample_end_offset);
            }
            else
            {
                v_ifh_retrigger(
                    &f_audio_item->sample_read_heads[f_send_num],
                    f_audio_item->sample_start_offset);
            }

            v_svf_reset(&f_audio_item->lp_filters[f_send_num]);

            v_adsr_retrigger(&f_audio_item->adsrs[f_send_num]);

            double f_diff = (a_ts->ml_next_beat - a_ts->ml_current_beat);
            double f_distance = f_audio_start - a_ts->ml_current_beat;

            f_i2 = (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            if(f_i2 < 0)
            {
                f_i2 = 0;
            }
            else if(f_i2 >= a_sample_count)
            {
                f_i2 = a_sample_count - 1;
            }
        }

        if((f_audio_item->adsrs[f_send_num].stage) != ADSR_STAGE_OFF)
        {
            while((f_i2 < a_sample_count) &&
                (((!f_audio_item->is_reversed) &&
                ((f_audio_item->sample_read_heads[
                    f_send_num].whole_number) <
                (f_audio_item->sample_end_offset)))
                    ||
                ((f_audio_item->is_reversed) &&
                ((f_audio_item->sample_read_heads[
                    f_send_num].whole_number) >
                (f_audio_item->sample_start_offset)))
                ))
            {
                assert(f_i2 < a_sample_count);
                v_pydaw_audio_item_set_fade_vol(f_audio_item, f_send_num);

                if(f_audio_item->wav_pool_item->channels == 1)
                {
                    float f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                    (f_audio_item->wav_pool_item->samples[0]),
                    (f_audio_item->sample_read_heads[f_send_num].whole_number),
                    (f_audio_item->sample_read_heads[f_send_num].fraction)) *
                    (f_audio_item->adsrs[f_send_num].output) *
                    (f_audio_item->vols_linear[f_send_num]) *
                    (f_audio_item->fade_vols[f_send_num]);

                    float f_tmp_sample1 = f_tmp_sample0;

                    if(f_audio_item->paif && f_audio_item->paif->loaded)
                    {
                        int f_i3;
                        for(f_i3 = 0; f_i3 < 8; ++f_i3)
                        {
                            f_paif_item = f_audio_item->paif->items[f_i3];
                            f_paif_item->func_ptr(f_paif_item->mf3,
                                f_tmp_sample0, f_tmp_sample1);
                            f_tmp_sample0 = f_paif_item->mf3->output0;
                            f_tmp_sample1 = f_paif_item->mf3->output1;
                        }
                    }

                    f_buff[0][f_i2] += f_tmp_sample0;
                    f_buff[1][f_i2] += f_tmp_sample1;
                }
                else if(f_audio_item->wav_pool_item->channels == 2)
                {
                    assert(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        <= f_audio_item->wav_pool_item->length);

                    assert(
                        f_audio_item->sample_read_heads[f_send_num].whole_number
                        >= PYDAW_AUDIO_ITEM_PADDING_DIV2);

                    float f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                        f_audio_item->wav_pool_item->samples[0],
                        f_audio_item->sample_read_heads[
                            f_send_num].whole_number,
                        f_audio_item->sample_read_heads[f_send_num].fraction) *
                        f_audio_item->adsrs[f_send_num].output *
                        f_audio_item->vols_linear[f_send_num] *
                        f_audio_item->fade_vols[f_send_num];

                    float f_tmp_sample1 = f_cubic_interpolate_ptr_ifh(
                        f_audio_item->wav_pool_item->samples[1],
                        f_audio_item->sample_read_heads[
                            f_send_num].whole_number,
                        f_audio_item->sample_read_heads[f_send_num].fraction) *
                    f_audio_item->adsrs[f_send_num].output *
                    f_audio_item->vols_linear[f_send_num]
                    * f_audio_item->fade_vols[f_send_num];


                    if(f_audio_item->paif && f_audio_item->paif->loaded)
                    {
                        int f_i3 = 0;
                        while(f_i3 < 8)
                        {
                            f_paif_item = f_audio_item->paif->items[f_i3];
                            f_paif_item->func_ptr(f_paif_item->mf3,
                                f_tmp_sample0, f_tmp_sample1);
                            f_tmp_sample0 = f_paif_item->mf3->output0;
                            f_tmp_sample1 = f_paif_item->mf3->output1;
                            ++f_i3;
                        }
                    }

                    f_buff[0][f_i2] += f_tmp_sample0;
                    f_buff[1][f_i2] += f_tmp_sample1;

                }
                else
                {
                    // TODO:  Catch this during load and
                    // do something then...
                    printf(
                        "Error: v_pydaw_dn_song->audio_items"
                        "[f_current_region]_run, invalid number "
                        "of channels %i\n",
                        f_audio_item->wav_pool_item->channels);
                }

                if(f_audio_item->is_reversed)
                {
                    v_ifh_run_reverse(
                        &f_audio_item->sample_read_heads[f_send_num],
                        f_audio_item->ratio);

                    if(f_audio_item->sample_read_heads[f_send_num].whole_number
                        < PYDAW_AUDIO_ITEM_PADDING_DIV2)
                    {
                        f_audio_item->adsrs[f_send_num].stage = ADSR_STAGE_OFF;
                    }
                }
                else
                {
                    v_ifh_run(
                        &f_audio_item->sample_read_heads[f_send_num],
                        f_audio_item->ratio);

                    if(f_audio_item->sample_read_heads[f_send_num].whole_number
                        >= f_audio_item->wav_pool_item->length - 1)
                    {
                        f_audio_item->adsrs[f_send_num].stage =
                            ADSR_STAGE_OFF;
                    }
                }


                if(f_audio_item->adsrs[f_send_num].stage == ADSR_STAGE_OFF)
                {
                    break;
                }

                v_adsr_run_db(&f_audio_item->adsrs[f_send_num]);

                ++f_i2;
            }//while < sample count
        }  //if stage
        ++f_i;
    } //while < audio item count
}

void g_dn_song_get(t_dawnext* self, int a_lock)
{
    t_dn_song * f_result;
    lmalloc((void**)&f_result, sizeof(t_dn_song));

    f_result->regions_atm = NULL;
    int f_i = 0;

    while(f_i < DN_MAX_REGION_COUNT)
    {
        f_result->regions[f_i] = NULL;
        ++f_i;
    }

    f_result->regions_atm = g_dn_atm_region_get(self);
    f_result->regions[0] = g_dn_region_get(self, 0);

    t_dn_song * f_old = self->en_song;

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    self->en_song = f_result;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(f_old)
    {
        v_dn_song_free(f_old);
    }

}


void v_dn_open_tracks()
{
    char f_file_name[1024];
    sprintf(f_file_name, "%s/projects/dawnext/tracks.txt",
        musikernel->project_folder);

    if(i_pydaw_file_exists(f_file_name))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(f_file_name,
                PYDAW_LARGE_STRING);

        while(1)
        {
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof)
            {
                break;
            }

            int f_track_index = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_solo = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);
            int f_mute = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);  //ignored
            v_iterate_2d_char_array(f_2d_array); //ignored

            assert(f_track_index >= 0 && f_track_index < DN_TRACK_COUNT);
            assert(f_solo == 0 || f_solo == 1);
            assert(f_mute == 0 || f_mute == 1);

            v_pydaw_open_track(dawnext->track_pool[f_track_index],
                dawnext->tracks_folder, f_track_index);

            dawnext->track_pool[f_track_index]->solo = f_solo;
            dawnext->track_pool[f_track_index]->mute = f_mute;
        }

        g_free_2d_char_array(f_2d_array);
    }
    else   //ensure everything is closed...
    {
        int f_i = 0;

        while(f_i < DN_TRACK_COUNT)
        {
            dawnext->track_pool[f_i]->solo = 0;
            dawnext->track_pool[f_i]->mute = 0;
            v_pydaw_open_track(dawnext->track_pool[f_i],
                dawnext->tracks_folder, f_i);
            ++f_i;
        }
    }
}


void v_dn_open_project(int a_first_load)
{
    sprintf(dawnext->project_folder, "%s/projects/dawnext",
        musikernel->project_folder);
    sprintf(dawnext->item_folder, "%s/items/",
        dawnext->project_folder);
    sprintf(dawnext->region_folder, "%s/regions/",
        dawnext->project_folder);
    sprintf(dawnext->tracks_folder, "%s/tracks",
        dawnext->project_folder);

    int f_i = 0;

    while(f_i < DN_MAX_ITEM_COUNT)
    {
        if(dawnext->item_pool[f_i])
        {
            free(dawnext->item_pool[f_i]);
            dawnext->item_pool[f_i] = NULL;
        }
        ++f_i;
    }

    //char f_song_file[1024];
    //sprintf(f_song_file,
    //    "%s/projects/dawnext/song.txt", musikernel->project_folder);

    struct stat f_proj_stat;
    stat((musikernel->project_folder), &f_proj_stat);
    struct stat f_item_stat;
    stat((dawnext->item_folder), &f_item_stat);
    struct stat f_reg_stat;
    stat((dawnext->region_folder), &f_reg_stat);
    //struct stat f_song_file_stat;
    //stat(f_song_file, &f_song_file_stat);

    //TODO:  This should be moved to a separate function
    char f_transport_file[1024];
    sprintf(f_transport_file, "%s/transport.txt", dawnext->project_folder);

    if(S_ISDIR(f_proj_stat.st_mode) &&
        S_ISDIR(f_item_stat.st_mode)
        //&& S_ISDIR(f_reg_stat.st_mode) && S_ISREG(f_song_file_stat.st_mode)
        )
    {
        t_dir_list * f_item_dir_list =
                g_get_dir_list(dawnext->item_folder);
        f_i = 0;

        while(f_i < f_item_dir_list->dir_count)
        {
            g_dn_item_get(dawnext, atoi(f_item_dir_list->dir_list[f_i]));
            ++f_i;
        }

        g_dn_song_get(dawnext, 0);

        if(a_first_load)
        {
            v_dn_open_tracks();
        }
    }
    else
    {
        printf("Song file and project directory structure not found, not "
                "loading project.  This is to be expected if launching PyDAW "
                "for the first time\n");
        //Loads empty...  TODO:  Make this a separate function for getting an
        //empty en_song or loading a file into one...
        g_dn_song_get(dawnext, 0);
    }

    if(i_pydaw_file_exists(f_transport_file))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
                f_transport_file, PYDAW_LARGE_STRING);
        v_iterate_2d_char_array(f_2d_array);
        float f_tempo = atof(f_2d_array->current_str);

        assert(f_tempo > 30.0f && f_tempo < 300.0f);
        v_dn_set_tempo(dawnext, f_tempo);
        g_free_2d_char_array(f_2d_array);
    }
    else  //No transport file, set default tempo
    {
        printf("No transport file found, defaulting to 128.0 BPM\n");
        v_dn_set_tempo(dawnext, 128.0f);
    }

    v_dn_update_track_send(dawnext, 0);

    v_dn_set_is_soloed(dawnext);

    v_dn_set_midi_devices();
}


int i_dn_song_index_from_region_uid(t_dawnext* self, int a_uid)
{
    int f_i = 0;

    while(f_i < DN_MAX_REGION_COUNT)
    {
        if(self->en_song->regions[f_i])
        {
            if(a_uid == self->en_song->regions[f_i]->uid)
            {
                return f_i;
            }
        }
        ++f_i;
    }
    return -1;
}

t_dn_atm_region * g_dn_atm_region_get(t_dawnext * self)
{
    t_dn_atm_region * f_result = NULL;

    char f_file[1024] = "\0";
    sprintf(f_file, "%s/automation.txt", self->project_folder);

    if(i_pydaw_file_exists(f_file))
    {
        lmalloc((void**)&f_result, sizeof(t_dn_atm_region));

        int f_i2;
        for(f_i2 = 0; f_i2 < MAX_PLUGIN_POOL_COUNT; ++f_i2)
        {
            f_result->plugins[f_i2].point_count = 0;
            f_result->plugins[f_i2].points = NULL;
        }

        t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_file,
            PYDAW_XLARGE_STRING); //TODO:  1MB big enough???

        int f_pos = 0;

        while(1)
        {
            v_iterate_2d_char_array(f_current_string);
            if(f_current_string->eof)
            {
                break;
            }

            if(f_current_string->current_str[0] == 'p')
            {
                v_iterate_2d_char_array(f_current_string);
                int f_index = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_count = atoi(f_current_string->current_str);

                assert(f_count >= 1 && f_count < 100000);  //sanity check

                f_result->plugins[f_index].point_count = f_count;
                lmalloc(
                    (void**)&f_result->plugins[f_index].points,
                    sizeof(t_dn_atm_point) * f_count);
                f_pos = 0;
            }
            else
            {
                double f_beat = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_port = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                float f_val = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_index = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_plugin = atoi(f_current_string->current_str);

                assert(f_pos < f_result->plugins[f_index].point_count);

                assert(f_result->plugins[f_index].points);

                t_dn_atm_point * f_point =
                    &f_result->plugins[f_index].points[f_pos];

                f_point->beat = f_beat;
                f_point->port = f_port;
                f_point->val = f_val;
                f_point->index = f_index;
                f_point->plugin = f_plugin;

                ++f_pos;
            }
        }

        g_free_2d_char_array(f_current_string);
    }

    return f_result;
}

void v_dn_atm_region_free(t_dn_atm_region * self)
{
    int f_i2 = 0;
    while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
    {
        if(self->plugins[f_i2].point_count)
        {
            free(self->plugins[f_i2].points);
        }
        ++f_i2;
    }

    free(self);
}

t_dn_region * g_dn_region_get(t_dawnext* self, int a_uid)
{
    t_dn_region * f_result;
    int f_item_counters[DN_TRACK_COUNT];
    lmalloc((void**)&f_result, sizeof(t_dn_region));

    f_result->tempo = 128.0f;
    f_result->region_length_bars = 0;
    f_result->region_length_beats = 0;
    f_result->bar_length = 0;
    f_result->uid = a_uid;

    int f_i = 0;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        f_result->tracks[f_i].refs = NULL;
        f_result->tracks[f_i].count = 0;
        f_result->tracks[f_i].pos = 0;
        f_item_counters[f_i] = 0;
    }


    char f_full_path[PYDAW_TINY_STRING];
    sprintf(f_full_path, "%s/sequencer.txt", self->project_folder); //, a_uid);
    //sprintf(f_full_path, "%s%i", self->region_folder, a_uid);

    t_2d_char_array * f_current_string =
        g_get_2d_array_from_file(f_full_path, PYDAW_LARGE_STRING);

    f_i = 0;

    while(1)
    {
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }

        char f_key = f_current_string->current_str[0];

        if(f_key == 'L')
        {
            v_iterate_2d_char_array(f_current_string);
            f_result->region_length_bars = atoi(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);
            f_result->bar_length = atoi(f_current_string->current_str);

            f_result->region_length_beats =
                f_result->region_length_bars * f_result->bar_length;
        }
        else if(f_key == 'T')
        {
            assert(NULL);  //tempo, not yet implemented
        }
        else if(f_key == 'C')
        {
            v_iterate_2d_char_array(f_current_string);
            int f_track_num = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);

            f_result->tracks[f_track_num].count =
                atoi(f_current_string->current_str);

            assert(!f_result->tracks[f_track_num].refs);

            lmalloc((void**)&f_result->tracks[f_track_num].refs,
                f_result->tracks[f_track_num].count * sizeof(t_dn_item_ref));
        }
        else
        {
            int f_track_num = atoi(f_current_string->current_str);

            assert(f_result->tracks[f_track_num].refs);

            t_dn_item_ref * f_item_ref =
                &f_result->tracks[f_track_num].refs[
                    f_item_counters[f_track_num]];

            assert(f_item_counters[f_track_num] <
                f_result->tracks[f_track_num].count);

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->start = atof(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->length = atof(f_current_string->current_str);

            f_item_ref->end = f_item_ref->start + f_item_ref->length;

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->item_uid = atoi(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);
            f_item_ref->start_offset = atof(f_current_string->current_str);

            ++f_item_counters[f_track_num];
        }

        ++f_i;
    }

    g_free_2d_char_array(f_current_string);

    //v_pydaw_assert_memory_integrity(self);

    return f_result;
}


void g_dn_item_get(t_dawnext* self, int a_uid)
{
    float f_sr = musikernel->thread_storage[0].sample_rate;

    t_dn_item * f_result;
    lmalloc((void**)&f_result, sizeof(t_dn_item));

    f_result->event_count = 0;
    f_result->uid = a_uid;

    char f_full_path[2048];
    sprintf(f_full_path, "%s%i", self->item_folder, a_uid);

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_full_path,
            PYDAW_LARGE_STRING);

    int f_i = 0;

    f_result->audio_items = g_pydaw_audio_items_get(
        musikernel->thread_storage[0].sample_rate);

    while(f_i < DN_MAX_EVENTS_PER_ITEM_COUNT)
    {
        v_iterate_2d_char_array(f_current_string);

        if(f_current_string->eof)
        {
            break;
        }

        char f_type = f_current_string->current_str[0];

        if(f_type == 'n')  //note
        {
            v_iterate_2d_char_array(f_current_string);
            float f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            float f_length = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_note = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_vel = atoi(f_current_string->current_str);
            assert((f_result->event_count) < DN_MAX_EVENTS_PER_ITEM_COUNT);
            g_pynote_init(&f_result->events[(f_result->event_count)],
                    f_note, f_vel, f_start, f_length);
            ++f_result->event_count;
        }
        else if(f_type == 'c') //cc
        {
            v_iterate_2d_char_array(f_current_string);
            float f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_cc_num = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            float f_cc_val = atof(f_current_string->current_str);

            g_pycc_init(&f_result->events[(f_result->event_count)],
                f_cc_num, f_cc_val, f_start);
            ++f_result->event_count;
        }
        else if(f_type == 'p') //pitchbend
        {
            v_iterate_2d_char_array(f_current_string);
            float f_start = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            float f_pb_val = atof(f_current_string->current_str) * 8192.0f;

            g_pypitchbend_init(&f_result->events[(f_result->event_count)],
                    f_start, f_pb_val);
            ++f_result->event_count;
        }
        else if(f_type == 'a') //audio item
        {
            t_pydaw_audio_item * f_new =
                g_audio_item_load_single(f_sr,
                    f_current_string, 0, musikernel->wav_pool, 0);
            if(!f_new)  //EOF'd...
            {
                break;
            }

            t_pydaw_audio_items * f_audio_items =
                f_result->audio_items;

            int f_global_index = f_new->outputs[0];
            int f_index_count =
                f_audio_items->index_counts[f_global_index];

            f_audio_items->indexes[
                f_global_index][f_index_count].item_num = f_new->index;
            f_audio_items->indexes[
                f_global_index][f_index_count].send_num = 0;
            ++f_audio_items->index_counts[f_global_index];

            int f_i2;

            for(f_i2 = 1; f_i2 < 3; ++f_i2)
            {
                f_global_index = f_new->outputs[f_i2];
                if(f_global_index > -1)
                {
                    f_audio_items->indexes[f_global_index][
                        f_index_count].item_num = f_new->index;
                    f_audio_items->indexes[f_global_index][
                        f_index_count].send_num = f_i2;
                    ++f_audio_items->index_counts[f_global_index];
                }
            }

            f_audio_items->items[f_new->index] = f_new;
        }
        else if(f_type == 'f') //per-item-fx
        {
            v_iterate_2d_char_array(f_current_string);
            int f_index = atoi(f_current_string->current_str);
            t_paif * f_paif = g_paif8_get();
            f_result->audio_items->items[f_index]->paif = f_paif;
            f_paif->loaded = 1;

            int f_i2 = 0;

            while(f_i2 < 8)
            {
                f_paif->items[f_i2] = g_paif_get(f_sr);
                int f_i3 = 0;
                while(f_i3 < 3)
                {
                    v_iterate_2d_char_array(f_current_string);
                    float f_knob_val = atof(f_current_string->current_str);
                    f_paif->items[f_i2]->a_knobs[f_i3] = f_knob_val;
                    ++f_i3;
                }
                v_iterate_2d_char_array(f_current_string);
                int f_type_val = atoi(f_current_string->current_str);
                f_paif->items[f_i2]->fx_type = f_type_val;
                f_paif->items[f_i2]->func_ptr =
                        g_mf3_get_function_pointer(f_type_val);
                v_mf3_set(f_paif->items[f_i2]->mf3,
                        f_paif->items[f_i2]->a_knobs[0],
                        f_paif->items[f_i2]->a_knobs[1],
                        f_paif->items[f_i2]->a_knobs[2]);
                ++f_i2;
            }
        }
        else if(f_type == 'U')
        {
            v_iterate_2d_char_array(f_current_string);
            f_result->uid = atoi(f_current_string->current_str);
            assert(f_result->uid == a_uid);
        }
        else
        {
            printf("Invalid event type %c\n", f_type);
        }
        ++f_i;
    }

    g_free_2d_char_array(f_current_string);

    if(self->item_pool[a_uid])
    {
        free(self->item_pool[a_uid]);
    }

    self->item_pool[a_uid] = f_result;
}

t_dawnext * g_dawnext_get()
{
    t_dawnext * f_result;
    clalloc((void**)&f_result, sizeof(t_dawnext));

    f_result->current_sample = 0;
    f_result->current_region = 0;
    f_result->playback_inc = 0.0f;

    f_result->overdub_mode = 0;
    f_result->loop_mode = 0;

    f_result->project_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->item_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->region_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->tracks_folder = (char*)malloc(sizeof(char) * 1024);

    f_result->en_song = NULL;
    f_result->is_soloed = 0;
    f_result->suppress_new_audio_items = 0;

    f_result->ts[0].ml_sample_period_inc_beats = 0.0f;

    f_result->ts[0].ml_current_region = 0;
    f_result->ts[0].ml_next_region = 0;
    f_result->ts[0].ml_current_beat = 0.0f;
    f_result->ts[0].ml_next_beat = 0.0f;
    f_result->ts[0].ml_is_looping = 0;

    f_result->routing_graph = 0;

    int f_i = 0;
    int f_track_total = 0;


    while(f_i < DN_TRACK_COUNT)
    {
        f_result->track_pool[f_track_total] = g_pytrack_get(
            f_i, musikernel->thread_storage[0].sample_rate);
        ++f_i;
        ++f_track_total;
    }

    f_i = 0;

    while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
    {
        f_result->audio_glue_indexes[f_i] = 0;
        ++f_i;
    }

    f_i = 0;

    while(f_i < DN_MAX_ITEM_COUNT)
    {
        f_result->item_pool[f_i] = NULL;
        ++f_i;
    }

    g_dn_midi_routing_list_init(&f_result->midi_routing);

    return f_result;
}

/* void v_dn_set_playback_mode(t_pydaw_data * self,
 * int a_mode, //
 * int a_region, //The region index to start playback on
 * int a_bar) //The bar index (with a_region) to start playback on
 */
void v_dn_set_playback_mode(t_dawnext * self, int a_mode,
        double a_beat, int a_lock)
{
    switch(a_mode)
    {
        case 0: //stop
        {
            register int f_i = 0;
            int f_i2;
            t_pytrack * f_track;

            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            self->suppress_new_audio_items = 1;
            /*
            //Fade out the playing audio tracks
            if(self->en_song->audio_items[self->current_region])
            {
                while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
                {
                    if(self->en_song->audio_items[
                            self->current_region]->items[f_i])
                    {
                        for(f_i2 = 0; f_i2 < MK_AUDIO_ITEM_SEND_COUNT; ++f_i2)
                        {
                            v_adsr_release(&self->en_song->audio_items[
                                self->current_region]->items[f_i]->adsrs[f_i2]);
                        }
                    }
                    ++f_i;
                }
            }
            */

            self->suppress_new_audio_items = 0;
            musikernel->playback_mode = a_mode;

            f_i = 0;

            t_pydaw_plugin * f_plugin;

            while(f_i < DN_TRACK_COUNT)
            {
                f_i2 = 0;
                f_track = self->track_pool[f_i];

                f_track->period_event_index = 0;

                while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
                {
                    f_plugin = f_track->plugins[f_i2];
                    if(f_plugin)
                    {
                        f_plugin->descriptor->on_stop(f_plugin->PYFX_handle);
                    }
                    ++f_i2;
                }

                f_track->item_event_index = 0;

                ++f_i;
            }

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }

        }
            break;
        case 1:  //play
        {
            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            v_dn_set_playback_cursor(self, a_beat);

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }

            break;
        }
        case 2:  //record
            if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                return;
            }
            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            v_dn_set_playback_cursor(self, a_beat);

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }
            break;
    }
}

void v_dn_set_playback_cursor(t_dawnext * self, double a_beat)
{
    //self->current_region = a_region;
    self->ts[0].ml_next_beat = a_beat;
    t_dn_region * f_region = self->en_song->regions[0];

    register int f_i;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        self->track_pool[f_i]->item_event_index = 0;
        if((self->is_soloed && !self->track_pool[f_i]->solo) ||
            (self->track_pool[f_i]->mute))
        {
            self->track_pool[f_i]->fade_state = FADE_STATE_FADED;
        }

        f_region->tracks[f_i].pos = 0;
    }

    f_i = 0;

    while(f_i < MAX_PLUGIN_TOTAL_COUNT)
    {
        musikernel->plugin_pool[f_i].atm_pos = 0;
        ++f_i;
    }
}

void v_dn_set_is_soloed(t_dawnext * self)
{
    int f_i = 0;
    self->is_soloed = 0;

    while(f_i < DN_TRACK_COUNT)
    {
        if(self->track_pool[f_i]->solo)
        {
            self->is_soloed = 1;
            break;
        }
        ++f_i;
    }
}

void v_dn_set_loop_mode(t_dawnext * self, int a_mode)
{
    self->loop_mode = a_mode;
}

void v_dn_set_tempo(t_dawnext * self, float a_tempo)
{
    float f_sample_rate = musikernel->thread_storage[0].sample_rate;
    self->en_song->regions[0]->tempo = a_tempo;
    self->playback_inc = (1.0f / f_sample_rate) / (60.0f / a_tempo);
    self->samples_per_beat = (f_sample_rate) / (a_tempo / 60.0f);
}

void v_dn_offline_render_prep(t_dawnext * self)
{
    printf("Warming up plugins for offline rendering...\n");
    register int f_i = 0;
    t_pytrack * f_track;
    t_pydaw_plugin * f_plugin;

    while(f_i < DN_TRACK_COUNT)
    {
        f_track = self->track_pool[f_i];
        int f_i2 = 0;
        while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
        {
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->offline_render_prep)
            {
                f_plugin->descriptor->offline_render_prep(
                    f_plugin->PYFX_handle);
            }
            ++f_i2;
        }
        ++f_i;
    }
    printf("Finished warming up plugins\n");
}

void v_dn_offline_render(t_dawnext * self, double a_start_beat,
        double a_end_beat, char * a_file_out, int a_is_audio_glue,
        int a_create_file, t_dn_item_ref * a_glue_item)
{
    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 1;
    pthread_spin_unlock(&musikernel->main_lock);

    float f_sample_rate = musikernel->thread_storage[0].sample_rate;

    register int f_i;
    int f_beat_total = (int)(a_end_beat - a_start_beat);

    float f_sample_count =
        self->samples_per_beat * ((float)f_beat_total);

    long f_size = 0;
    long f_block_size = (musikernel->sample_count);

    float * f_output = (float*)malloc(sizeof(float) * (f_block_size * 2));

    float ** f_buffer;
    lmalloc((void**)&f_buffer, sizeof(float*) * 2);

    f_i = 0;
    while(f_i < 2)
    {
        lmalloc((void**)&f_buffer[f_i], sizeof(float) * f_block_size);
        ++f_i;
    }

    //We must set it back afterwards, or the UI will be wrong...
    int f_old_loop_mode = self->loop_mode;
    v_dn_set_loop_mode(self, DN_LOOP_MODE_OFF);

    v_dn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_PLAY, a_start_beat, 0);

    printf("\nOpening SNDFILE with sample rate %i\n", (int)f_sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(f_sample_rate);

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    printf("\nSuccessfully opened SNDFILE\n\n");

    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);

    while(self->ts[0].ml_current_beat < a_end_beat)
    {
        f_i = 0;
        f_size = 0;

        while(f_i < f_block_size)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
            ++f_i;
        }

        if(a_is_audio_glue)
        {
            v_dn_set_time_params(self, f_block_size);
            v_dn_audio_items_run(
                self, a_glue_item, f_block_size, f_buffer, NULL, -1, 1, NULL,
                &self->ts[0]);
            v_dn_finish_time_params(self);
        }
        else
        {
            v_dn_run_engine(f_block_size, f_buffer, NULL);
        }

        f_i = 0;
        /*Interleave the samples...*/
        while(f_i < f_block_size)
        {
            f_output[f_size] = f_buffer[0][f_i];
            ++f_size;
            f_output[f_size] = f_buffer[1][f_i];
            ++f_size;
            ++f_i;
        }

        if(a_create_file)
        {
            sf_writef_float(f_sndfile, f_output, f_block_size);
        }
    }

    clock_gettime(CLOCK_REALTIME, &f_finish);
    float f_elapsed = (float)v_pydaw_print_benchmark(
        "v_dn_offline_render", f_start, f_finish);
    float f_realtime = f_sample_count / f_sample_rate;

    printf("Realtime: %f\n", f_realtime);

    if(f_elapsed > 0.0f)
    {
        printf("Ratio:  %f : 1\n\n", f_realtime / f_elapsed);
    }
    else
    {
        printf("Ratio:  infinity : 1");
    }

    v_dn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_OFF, a_start_beat, 0);
    v_dn_set_loop_mode(self, f_old_loop_mode);

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_buffer);
    free(f_output);

    char f_tmp_finished[1024];

    sprintf(f_tmp_finished, "%s.finished", a_file_out);

    v_pydaw_write_to_file(f_tmp_finished, "finished");

    v_dn_panic(self);  //ensure all notes are off before returning

    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 0;
    pthread_spin_unlock(&musikernel->main_lock);
}


void v_dn_update_track_send(t_dawnext * self, int a_lock)
{
    t_dn_routing_graph * f_graph = g_dn_routing_graph_get(self);
    t_dn_routing_graph * f_old = self->routing_graph;

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    self->routing_graph = f_graph;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(f_old)
    {
        v_dn_routing_graph_free(f_old);
    }
}

void v_dn_routing_graph_free(t_dn_routing_graph * self)
{
    free(self);
}

t_dn_routing_graph * g_dn_routing_graph_get(t_dawnext * self)
{
    t_dn_routing_graph * f_result = NULL;
    lmalloc((void**)&f_result, sizeof(t_dn_routing_graph));

    int f_i = 0;
    int f_i2 = 0;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        for(f_i2 = 0; f_i2 < MAX_WORKER_THREADS; ++f_i2)
        {
            f_result->track_pool_sorted[f_i2][f_i] = 0;
            f_result->bus_count[f_i] = 0;
        }

        for(f_i2 = 0; f_i2 < MAX_ROUTING_COUNT; ++f_i2)
        {
            f_result->routes[f_i][f_i2].active = 0;
        }
    }

    f_result->track_pool_sorted_count = 0;

    char f_tmp[1024];
    sprintf(f_tmp, "%s/projects/dawnext/routing.txt",
        musikernel->project_folder);

    if(i_pydaw_file_exists(f_tmp))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
        f_tmp, PYDAW_LARGE_STRING);
        while(1)
        {
            v_iterate_2d_char_array(f_2d_array);
            if(f_2d_array->eof)
            {
                break;
            }

            if(f_2d_array->current_str[0] == 't')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i)
                {
                    f_result->track_pool_sorted[f_i][f_index] = f_track_num;
                }

            }
            else if(f_2d_array->current_str[0] == 's')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_output = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_sidechain = atoi(f_2d_array->current_str);

                v_pytrack_routing_set(
                    &f_result->routes[f_track_num][f_index], f_output,
                    f_sidechain);
                ++f_result->bus_count[f_output];
            }
            else if(f_2d_array->current_str[0] == 'c')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_count = atoi(f_2d_array->current_str);
                f_result->track_pool_sorted_count = f_count;
            }
            else
            {
                assert(0);
            }
        }
        g_free_2d_char_array(f_2d_array);
    }

    return f_result;
}

void v_dn_set_midi_device(int a_on, int a_device, int a_output)
{
    t_dawnext * self = dawnext;
    /* Interim logic to get a minimum viable product working
     * TODO:  Make it modular and able to support multiple devices
     */
    t_dn_midi_routing_list * f_list = &self->midi_routing;
    t_pydaw_midi_routing * f_route = &f_list->routes[a_device];
    t_pytrack * f_track_old = NULL;
    t_pytrack * f_track_new = self->track_pool[a_output];

    if(f_route->output_track != -1)
    {
        f_track_old = self->track_pool[f_route->output_track];
    }

    if(f_track_old && (!f_route->on || f_route->output_track != a_output))
    {
        f_track_old->extern_midi = 0;
        f_track_old->extern_midi_count = &ZERO;
        f_track_old->midi_device = 0;
    }

    f_route->on = a_on;
    f_route->output_track = a_output;

    if(f_route->on && musikernel->midi_devices->devices[a_device].loaded)
    {
        f_track_new->midi_device = &musikernel->midi_devices->devices[a_device];
        f_track_new->extern_midi =
            musikernel->midi_devices->devices[a_device].instanceEventBuffers;

        midiPoll(f_track_new->midi_device);
        midiDeviceRead(f_track_new->midi_device,
            musikernel->thread_storage[0].sample_rate, 512);

        musikernel->midi_devices->devices[a_device].instanceEventCounts = 0;
        musikernel->midi_devices->devices[a_device].midiEventReadIndex = 0;
        musikernel->midi_devices->devices[a_device].midiEventWriteIndex = 0;

        f_track_new->extern_midi_count =
            &musikernel->midi_devices->devices[a_device].instanceEventCounts;
    }
    else
    {
        f_track_new->extern_midi = 0;
        f_track_new->extern_midi_count = &ZERO;
        f_track_new->midi_device = 0;
    }
}


void v_dn_set_midi_devices()
{
    char f_path[2048];
    int f_i, f_i2;
    t_midi_device * f_device;

    if(!musikernel->midi_devices)
    {
        return;
    }

    sprintf(f_path, "%s/projects/dawnext/midi_routing.txt",
        musikernel->project_folder);

    if(!i_pydaw_file_exists(f_path))
    {
        return;
    }

    t_2d_char_array * f_current_string =
        g_get_2d_array_from_file(f_path, PYDAW_LARGE_STRING);

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }

        int f_on = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);
        int f_track_num = atoi(f_current_string->current_str);

        v_iterate_2d_char_array_to_next_line(f_current_string);

        for(f_i2 = 0; f_i2 < musikernel->midi_devices->count; ++f_i2)
        {
            f_device = &musikernel->midi_devices->devices[f_i2];
            if(!strcmp(f_current_string->current_str, f_device->name))
            {
                v_dn_set_midi_device(f_on, f_i2, f_track_num);
                break;
            }
        }
    }

    g_free_2d_char_array(f_current_string);
}


void v_dn_configure(const char* a_key, const char* a_value)
{
    t_dawnext * self = dawnext;
    printf("v_dn_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, DN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX))
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 4,
                PYDAW_SMALL_STRING);
        int f_item_index = atoi(f_arr->array[0]);
        assert(NULL);  // The below hasn't been added to the UI
        int f_audio_item_index = atoi(f_arr->array[1]);
        int f_port_num = atoi(f_arr->array[2]);
        float f_port_val = atof(f_arr->array[3]);

        v_dn_paif_set_control(self, f_item_index, f_audio_item_index,
                f_port_num, f_port_val);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_DN_PLAYBACK))
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_mode = atoi(f_arr->array[0]);
        assert(f_mode >= 0 && f_mode <= 2);
        double f_beat = atof(f_arr->array[1]);
        v_dn_set_playback_mode(self, f_mode, f_beat, 1);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SR))
    {
        //Ensure that a project isn't being loaded right now
        pthread_spin_lock(&musikernel->main_lock);
        pthread_spin_unlock(&musikernel->main_lock);

        int f_uid = atoi(a_value);
        t_dn_region * f_result = g_dn_region_get(self, f_uid);
        int f_region_index = i_dn_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_dn_region * f_old_region = NULL;
            if(self->en_song->regions[f_region_index])
            {
                f_old_region = self->en_song->regions[f_region_index];
            }
            pthread_spin_lock(&musikernel->main_lock);
            self->en_song->regions[f_region_index] = f_result;
            pthread_spin_unlock(&musikernel->main_lock);
            if(f_old_region)
            {
                free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SI)) //Save Item
    {
        pthread_spin_lock(&musikernel->main_lock);
        g_dn_item_get(self, atoi(a_value));
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SS))  //Save Song
    {
        g_dn_song_get(self, 1);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SAVE_ATM))
    {
        int f_uid = atoi(a_value);
        t_dn_atm_region * f_result = g_dn_atm_region_get(self);
        int f_region_index = i_dn_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_dn_atm_region * f_old_region = NULL;
            if(self->en_song->regions_atm)
            {
                f_old_region = self->en_song->regions_atm;
            }
            pthread_spin_lock(&musikernel->main_lock);
            self->en_song->regions_atm = f_result;
            pthread_spin_unlock(&musikernel->main_lock);
            if(f_old_region)
            {
                v_dn_atm_region_free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_LOOP)) //Set loop mode
    {
        int f_value = atoi(a_value);

        pthread_spin_lock(&musikernel->main_lock);
        v_dn_set_loop_mode(self, f_value);
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_OS)) //Open Song
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        int f_first_open = atoi(f_kvp->key);
        v_dn_open_project(f_first_open);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_TEMPO)) //Change tempo
    {
        pthread_spin_lock(&musikernel->main_lock);
        v_dn_set_tempo(self, atof(a_value));
        pthread_spin_unlock(&musikernel->main_lock);
        //To reload audio items when tempo changed
        //g_dn_song_get(self);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SOLO)) //Set track solo
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);

        pthread_spin_lock(&musikernel->main_lock);

        self->track_pool[f_track_num]->solo = f_mode;
        //self->track_pool[f_track_num]->period_event_index = 0;

        v_dn_set_is_soloed(self);

        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_MUTE)) //Set track mute
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);
        pthread_spin_lock(&musikernel->main_lock);

        self->track_pool[f_track_num]->mute = f_mode;
        //self->track_pool[f_track_num]->period_event_index = 0;

        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_PLUGIN_INDEX))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 5,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_plugin_index = atoi(f_val_arr->array[2]);
        int f_plugin_uid = atoi(f_val_arr->array[3]);
        int f_power = atoi(f_val_arr->array[4]);

        t_pytrack * f_track = dawnext->track_pool[f_track_num];

        v_pydaw_set_plugin_index(
            f_track, f_index, f_plugin_index, f_plugin_uid, f_power, 1);

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_UPDATE_SEND))
    {
        v_dn_update_track_send(self, 1);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SET_OVERDUB_MODE))
    {
        int f_bool = atoi(a_value);
        assert(f_bool == 0 || f_bool == 1);
        pthread_spin_lock(&musikernel->main_lock);
        self->overdub_mode = f_bool;
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_GLUE_AUDIO_ITEMS))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        char * f_path = f_val_arr->str_arr[0];  //Don't free this
        double f_start_beat = atof(f_val_arr->str_arr[1]);
        double f_end_beat = atof(f_val_arr->str_arr[2]);
        int f_item_uid = atoi(f_val_arr->str_arr[3]);

        int f_i = 0;
        while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
        {
            self->audio_glue_indexes[f_i] = 0;
            ++f_i;
        }

        f_i = 4;
        while(f_i < f_val_arr->count)
        {
            int f_index = atoi(f_val_arr->str_arr[f_i]);
            self->audio_glue_indexes[f_index] = 1;
            ++f_i;
        }

        t_dn_item_ref f_item_ref;
        f_item_ref.item_uid = f_item_uid;
        f_item_ref.start = 0.0d;
        f_item_ref.end = f_end_beat;

        v_dn_offline_render(self, f_start_beat, f_end_beat,
            f_path, 1, 1, &f_item_ref);

        v_free_split_line(f_val_arr);

    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_PANIC))
    {
        pthread_spin_lock(&musikernel->main_lock);
        musikernel->is_offline_rendering = 1;
        pthread_spin_unlock(&musikernel->main_lock);

        v_dn_panic(self);

        pthread_spin_lock(&musikernel->main_lock);
        musikernel->is_offline_rendering = 0;
        pthread_spin_unlock(&musikernel->main_lock);

    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_SET_POS))
    {
        if(musikernel->playback_mode != 0)
        {
            return;
        }

        double f_beat = atof(a_value);

        pthread_spin_lock(&musikernel->main_lock);
        v_dn_set_playback_cursor(self, f_beat);
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, DN_CONFIGURE_KEY_MIDI_DEVICE))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        int f_on = atoi(f_val_arr->str_arr[0]);
        int f_device = atoi(f_val_arr->str_arr[1]);
        int f_output = atoi(f_val_arr->str_arr[2]);
        v_free_split_line(f_val_arr);

        pthread_spin_lock(&musikernel->main_lock);

        v_dn_set_midi_device(f_on, f_device, f_output);

        pthread_spin_unlock(&musikernel->main_lock);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }
}

#endif	/* DAWNEXT_H */

