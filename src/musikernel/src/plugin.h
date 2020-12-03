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

#ifndef PYDAW_PLUGIN_HEADER_INCLUDED
#define PYDAW_PLUGIN_HEADER_INCLUDED

#include <pthread.h>
#include <assert.h>
#include "files.h"
#include "libmodsynth/lib/lmalloc.h"

#define PYDAW_EVENT_NOTEON     0
#define PYDAW_EVENT_NOTEOFF    1
#define PYDAW_EVENT_PITCHBEND  2
#define PYDAW_EVENT_CONTROLLER 3
#define PYDAW_EVENT_AUTOMATION 4

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*fp_queue_message)(char*, char*);

typedef MKFLT PYFX_Data;

typedef int PYFX_PortDescriptor;


typedef struct _PYFX_PortRangeHint {
  PYFX_Data DefaultValue;
  PYFX_Data LowerBound;
  PYFX_Data UpperBound;
} PYFX_PortRangeHint;

typedef void * PYFX_Handle;

// MIDI event
typedef struct
{
	int type;               /**< event type */
	int tick;	        /**< tick-time */
	unsigned int tv_sec;	/**< seconds */
	unsigned int tv_nsec;	/**< nanoseconds */
        int channel;		/**< channel number */
	int note;		/**< note */
	int velocity;		/**< velocity */
	int duration;		/**< duration until note-off;
                                 * only for #PYDAW_EVENT_NOTEON */
	int param;		/**< control parameter */
        MKFLT value;
        MKFLT start;
        MKFLT length;
        int port;
} t_seq_event;

typedef struct
{
    int uid;
    MKFLT * samples[2];
    MKFLT ratio_orig;
    int channels;
    int length;
    MKFLT sample_rate;
    int is_loaded;  //wav's are now loaded dynamically when they are first seen
    MKFLT host_sr;  //host sample-rate, cached here for easy access
    char path[2048];
}t_wav_pool_item;

typedef t_wav_pool_item * (*fp_get_wavpool_item_from_host)(int);

/* For sorting a list by start time */
int seq_event_cmpfunc(void *self, void *other)
{
    t_seq_event *self_ev = (t_seq_event*)self;
    t_seq_event *other_ev = (t_seq_event*)other;

    return self_ev->tick < other_ev->tick;
}

/* Descriptor for a Type of Plugin:

   This structure is used to describe a plugin type. It provides a
   number of functions to examine the type, instantiate it, link it to
   buffers and workspaces and to run it. */

typedef struct _PYFX_Descriptor {
    int PortCount;

    PYFX_PortDescriptor * PortDescriptors;

    /* This member indicates an array of range hints for each port (see
     above). Valid indices vary from 0 to PortCount-1. */
    PYFX_PortRangeHint * PortRangeHints;

    PYFX_Handle (*instantiate)(struct _PYFX_Descriptor * Descriptor,
        int SampleRate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message);

    void (*connect_port)(PYFX_Handle Instance, int Port,
        PYFX_Data * DataLocation);

    /* Assign the audio buffer at DataLocation to index a_index
     */
    void (*connect_buffer)(PYFX_Handle Instance, int a_index,
            MKFLT * DataLocation, int a_is_sidechain);

    void (*cleanup)(PYFX_Handle Instance);

    /* Load the plugin state file at a_file_path
     */
    void (*load)(PYFX_Handle Instance, struct _PYFX_Descriptor * Descriptor,
            char * a_file_path);

    void (*set_port_value)(PYFX_Handle Instance, int a_port, MKFLT a_value);

    void (*set_cc_map)(PYFX_Handle Instance, char * a_msg);

    /* When a panic message is sent, do whatever it takes to fix any stuck
     notes. */
    void (*panic)(PYFX_Handle Instance);

    //For now all plugins must set it to 1.

    int API_Version;

    void (*configure)(PYFX_Handle Instance, char *Key, char *Value,
        pthread_spinlock_t * a_spinlock);

    // Plugins NOT part of a send channel will always call this
    void (*run_replacing)(
        PYFX_Handle Instance, int SampleCount,
        struct ShdsList * midi_events,
        struct ShdsList * atm_events);

    // Plugins that ARE part of a send channel will always call this,
    // any plugin that isn't a fader/channel type plugin do not need
    // to implement or set this
    void (*run_mixing)(
        PYFX_Handle Instance, int SampleCount,
        MKFLT ** output_buffers, int output_count,
        struct ShdsList * midi_events,
        struct ShdsList * atm_events);

    /* Do anything like warming up oscillators, etc...  in preparation
     * for offline rendering.  This must be called after loading
     * the project.
     */
    void (*offline_render_prep)(PYFX_Handle Instance);

    /* Force any notes to off, etc...  and anything else you may want to
     * do when the transport stops
     */
    void (*on_stop)(PYFX_Handle Instance);

} PYFX_Descriptor;

typedef PYFX_Descriptor * (*PYFX_Descriptor_Function)();

typedef struct
{
    int type;
    int tick;
    MKFLT value;
    int port;
}t_plugin_event_queue_item;

typedef struct
{
    int count;
    int pos;
    t_plugin_event_queue_item items[200];
}t_plugin_event_queue;

typedef struct
{
    int count;
    int ports[5];
    MKFLT lows[5];
    MKFLT highs[5];
}t_cc_mapping;

typedef struct
{
    t_cc_mapping map[128];
}t_plugin_cc_map;

void v_plugin_event_queue_add(t_plugin_event_queue*, int, int, MKFLT, int);
void v_plugin_event_queue_reset(t_plugin_event_queue*);
t_plugin_event_queue_item * v_plugin_event_queue_iter(
    t_plugin_event_queue*, int);
void v_plugin_event_queue_atm_set(t_plugin_event_queue*, int, MKFLT*);
inline MKFLT f_cc_to_ctrl_val(PYFX_Descriptor*, int, MKFLT);
void v_cc_mapping_init(t_cc_mapping*);
void v_cc_map_init(t_plugin_cc_map*);
void v_cc_map_translate(t_plugin_cc_map*, PYFX_Descriptor*, MKFLT*, int, MKFLT);
void v_generic_cc_map_set(t_plugin_cc_map*, char*);

#ifdef __cplusplus
}
#endif

void v_cc_mapping_init(t_cc_mapping* self)
{
    int f_i;
    self->count = 0;

    for(f_i = 0; f_i < 5; ++f_i)
    {
        self->lows[f_i] = 0.0f;
        self->highs[f_i] = 1.0f;
        self->ports[f_i] = -1;
    }
}

void v_cc_mapping_set(t_cc_mapping* self, int a_port, MKFLT a_low, MKFLT a_high)
{
    self->ports[self->count] = a_port;
    self->lows[self->count] = a_low;
    self->highs[self->count] = a_high;
    self->count++;
}

void v_cc_map_init(t_plugin_cc_map * self)
{
    int f_i = 0;
    while(f_i < 128)
    {
        v_cc_mapping_init(&self->map[f_i]);
        f_i++;
    }
}

void v_cc_map_translate(t_plugin_cc_map *self, PYFX_Descriptor *desc,
    MKFLT *a_port_table, int a_cc, MKFLT a_value)
{
    int f_i;
    a_value *= 0.007874f;  // a_val / 127.0f

    for(f_i = 0; f_i < self->map[a_cc].count; ++f_i)
    {
        int f_port = self->map[a_cc].ports[f_i];
        PYFX_PortRangeHint * f_range = &desc->PortRangeHints[f_port];
        MKFLT f_diff = f_range->UpperBound - f_range->LowerBound;
        MKFLT f_min = f_diff * self->map[a_cc].lows[f_i];
        MKFLT f_max = f_diff * self->map[a_cc].highs[f_i];
        a_port_table[f_port] = (a_value * (f_max - f_min)) +
            f_min + f_range->LowerBound;
    }
}

MKFLT f_atm_to_ctrl_val(PYFX_Descriptor *self, int a_port, MKFLT a_val)
{
    PYFX_PortRangeHint * f_range = &self->PortRangeHints[a_port];
    a_val *= 0.007874f;  // a_val / 127.0f
    return (a_val * (f_range->UpperBound - f_range->LowerBound)) +
        f_range->LowerBound;
}

void v_plugin_event_queue_add(
    t_plugin_event_queue *self, int a_type, int a_tick,
    MKFLT a_val, int a_port)
{
    t_plugin_event_queue_item * f_item = &self->items[self->count];
    f_item->type = a_type;
    f_item->tick = a_tick;
    f_item->value = a_val;
    f_item->port = a_port;
    ++self->count;
    assert(self->count <= 200);
}

void v_plugin_event_queue_reset(t_plugin_event_queue * self)
{
    self->pos = 0;
    self->count = 0;
}

t_plugin_event_queue_item * v_plugin_event_queue_iter(
    t_plugin_event_queue *self, int a_sample_num)
{
    t_plugin_event_queue_item * f_item = &self->items[self->pos];
    if(self->pos < self->count &&
       a_sample_num == f_item->tick)
    {
       ++self->pos;
       return f_item;
    }
    else
    {
        return 0;
    }
}

void v_plugin_event_queue_atm_set(
    t_plugin_event_queue *self, int a_sample_num, MKFLT * a_table)
{
    while(1)
    {
        t_plugin_event_queue_item * f_item =
            v_plugin_event_queue_iter(self, a_sample_num);
        if(!f_item)
        {
            break;
        }

        a_table[f_item->port] = f_item->value;
    }
}

inline void v_ev_clear(t_seq_event * a_event)
{
    a_event->type = -1;
    a_event->tick = 0;
}

inline void v_ev_set_pitchbend(t_seq_event* a_event,
        int a_channel, int a_value)
{
    a_event->type = PYDAW_EVENT_PITCHBEND;
    a_event->channel = a_channel;
    a_event->value = a_value;
}

inline void v_ev_set_noteoff(t_seq_event* a_event,
        int a_channel, int a_note, int a_velocity)
{
    a_event->type = PYDAW_EVENT_NOTEOFF;
    a_event->channel = a_channel;
    a_event->note = a_note;
    a_event->velocity = a_velocity;
}

inline void v_ev_set_noteon(t_seq_event* a_event,
        int a_channel, int a_note, int a_velocity)
{
    a_event->type = PYDAW_EVENT_NOTEON;
    a_event->channel = a_channel;
    a_event->note = a_note;
    a_event->velocity = a_velocity;
}

inline void v_ev_set_controller(t_seq_event* a_event,
        int a_channel, int a_cc_num, int a_value)
{
    a_event->type = PYDAW_EVENT_CONTROLLER;
    a_event->channel = a_channel;
    a_event->param = a_cc_num;
    a_event->value = a_value;
}

inline void v_ev_set_atm(t_seq_event* a_event,
        int a_port_num, int a_value)
{
    a_event->type = PYDAW_EVENT_AUTOMATION;
    a_event->channel = 0;
    a_event->port = a_port_num;
    a_event->value = a_value;
}

PYFX_Descriptor * get_pyfx_descriptor(int a_port_count)
{
    PYFX_Descriptor *f_result =
            (PYFX_Descriptor*)malloc(sizeof(PYFX_Descriptor));

    f_result->PortCount = a_port_count;

    f_result->PortDescriptors =
        (PYFX_PortDescriptor*)calloc(f_result->PortCount,
            sizeof(PYFX_PortDescriptor));

    f_result->PortRangeHints =
        (PYFX_PortRangeHint*)calloc(f_result->PortCount,
            sizeof(PYFX_PortRangeHint));

    return f_result;
}

void set_pyfx_port(PYFX_Descriptor * a_desc, int a_port,
        MKFLT a_default, MKFLT a_min, MKFLT a_max)
{
    assert(a_port >= 0 && a_port < a_desc->PortCount);
    assert(!a_desc->PortDescriptors[a_port]);
    assert(a_min < a_max);
    assert(a_default >= a_min && a_default <= a_max);

    a_desc->PortDescriptors[a_port] = 1;
    a_desc->PortRangeHints[a_port].DefaultValue = a_default;
    a_desc->PortRangeHints[a_port].LowerBound = a_min;
    a_desc->PortRangeHints[a_port].UpperBound = a_max;
}



PYFX_Data g_get_port_default(PYFX_Descriptor *plugin, int port)
{
    PYFX_PortRangeHint hint = plugin->PortRangeHints[port];
    assert(hint.DefaultValue <= hint.UpperBound &&
            hint.DefaultValue >= hint.LowerBound );
    return hint.DefaultValue;
}

MKFLT * g_get_port_table(PYFX_Handle * handle,
        PYFX_Descriptor * descriptor)
{
    MKFLT * pluginControlIns;
    int j;

    int f_i = 0;

    hpalloc((void**)(&pluginControlIns), sizeof(MKFLT) * descriptor->PortCount);

    f_i = 0;
    while(f_i < descriptor->PortCount)
    {
        pluginControlIns[f_i] = 0.0f;
        f_i++;
    }

    for (j = 0; j < descriptor->PortCount; j++)
    {
        PYFX_PortDescriptor pod = descriptor->PortDescriptors[j];

        if(pod)
        {
            pluginControlIns[j] = g_get_port_default(descriptor, j);

            descriptor->connect_port(handle, j, &pluginControlIns[j]);
        }
    }

    return pluginControlIns;
}

void v_generic_cc_map_set(t_plugin_cc_map * a_cc_map, char * a_str)
{
    t_2d_char_array * f_2d_array = g_get_2d_array(PYDAW_SMALL_STRING);
    f_2d_array->array = a_str;
    v_iterate_2d_char_array(f_2d_array);
    int f_cc = atoi(f_2d_array->current_str);

    v_iterate_2d_char_array(f_2d_array);
    int f_count = atoi(f_2d_array->current_str);
    a_cc_map->map[f_cc].count = f_count;

    int f_i = 0;
    while(f_i < f_count)
    {
        v_iterate_2d_char_array(f_2d_array);
        int f_port = atoi(f_2d_array->current_str);
        v_iterate_2d_char_array(f_2d_array);
        MKFLT f_low = atof(f_2d_array->current_str);
        v_iterate_2d_char_array(f_2d_array);
        MKFLT f_high = atof(f_2d_array->current_str);

        v_cc_mapping_set(&a_cc_map->map[f_cc], f_port, f_low, f_high);

        ++f_i;
    }
}

void generic_file_loader(PYFX_Handle Instance,
        PYFX_Descriptor * Descriptor, char * a_path, MKFLT * a_table,
        t_plugin_cc_map * a_cc_map)
{
    t_2d_char_array * f_2d_array = g_get_2d_array_from_file(a_path,
                PYDAW_LARGE_STRING);

    while(1)
    {
        v_iterate_2d_char_array(f_2d_array);

        if(f_2d_array->eof)
        {
            break;
        }

        assert(strcmp(f_2d_array->current_str, ""));

        if(f_2d_array->current_str[0] == 'c')
        {
            char * f_config_key = (char*)malloc(
                sizeof(char) * PYDAW_TINY_STRING);
            v_iterate_2d_char_array(f_2d_array);
            strcpy(f_config_key, f_2d_array->current_str);
            char * f_value = (char*)malloc(
                sizeof(char) * PYDAW_SMALL_STRING);
            v_iterate_2d_char_array_to_next_line(f_2d_array);
            strcpy(f_value, f_2d_array->current_str);

            Descriptor->configure(Instance, f_config_key, f_value, 0);

            free(f_config_key);
            free(f_value);
        }
        else if(f_2d_array->current_str[0] == 'm')
        {
            v_iterate_2d_char_array(f_2d_array);
            int f_cc = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_count = atoi(f_2d_array->current_str);

            int f_i = 0;
            while(f_i < f_count)
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_port = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                MKFLT f_low = atof(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                MKFLT f_high = atof(f_2d_array->current_str);

                v_cc_mapping_set(&a_cc_map->map[f_cc], f_port, f_low, f_high);
                ++f_i;
            }
        }
        else
        {
            int f_port_key = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array_to_next_line(f_2d_array);
            MKFLT f_port_value = atof(f_2d_array->current_str);

            assert(f_port_key >= 0);
            assert(f_port_key <= Descriptor->PortCount);

            a_table[f_port_key] = f_port_value;
        }
    }

    g_free_2d_char_array(f_2d_array);

}


#endif /* PYDAW_PLUGIN_HEADER_INCLUDED */
