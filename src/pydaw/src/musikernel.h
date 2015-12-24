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

#ifndef MUSIKERNEL_H
#define	MUSIKERNEL_H

#include <time.h>

#include "libshds.h"
#include "pydaw_files.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "pydaw_plugin_wrapper.h"
#include "pydaw_audio_inputs.h"

#ifndef NO_MIDI
    #include "midi_device.h"
#else
    #define t_midi_device void
    #define t_midi_device_list void

    void midiPoll(void * arg){}
    void midiDeviceRead(void * arg1, float arg2, int arg3){}
#endif

#define MAX_WORKER_THREADS 8

#define PYDAW_MAX_EVENT_BUFFER_SIZE 512

#define PYDAW_MIDI_NOTE_COUNT 128

#define MAX_PLUGIN_COUNT 10
#define MAX_ROUTING_COUNT 4
#define MAX_PLUGIN_TOTAL_COUNT (MAX_PLUGIN_COUNT + MAX_ROUTING_COUNT)

#define MAX_PLUGIN_POOL_COUNT 1000

#define MAX_AUDIO_INPUT_COUNT 128
int PYDAW_AUDIO_INPUT_TRACK_COUNT = 0;
int OUTPUT_CH_COUNT = 2;
int MASTER_OUT_L = 0;
int MASTER_OUT_R = 1;

#define PYDAW_OSC_SEND_QUEUE_SIZE 256
#define PYDAW_OSC_MAX_MESSAGE_SIZE 65536

#ifdef __linux__
    #define FRAMES_PER_BUFFER 4096
#else
    // Lest no low-latency back-end is available
    #define FRAMES_PER_BUFFER 8192
#endif

#define STATUS_NOT_PROCESSED 0
#define STATUS_PROCESSING 1
#define STATUS_PROCESSED 2

#define PYDAW_PLAYBACK_MODE_OFF 0
#define PYDAW_PLAYBACK_MODE_PLAY 1
#define PYDAW_PLAYBACK_MODE_REC 2

#define FADE_STATE_OFF 0
#define FADE_STATE_FADING 1
#define FADE_STATE_FADED 2
#define FADE_STATE_RETURNING 3

#define SEQ_EVENT_NONE 0
#define SEQ_EVENT_LOOP 1
#define SEQ_EVENT_TEMPO_CHANGE 2
#define SEQ_EVENT_MARKER 3

#define MK_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL "pc"
#define MK_CONFIGURE_KEY_CONFIGURE_PLUGIN "co"
#define MK_CONFIGURE_KEY_EXIT "exit"
#define MK_CONFIGURE_KEY_PITCH_ENV "penv"
#define MK_CONFIGURE_KEY_RATE_ENV "renv"
#define MK_CONFIGURE_KEY_PREVIEW_SAMPLE "preview"
#define MK_CONFIGURE_KEY_STOP_PREVIEW "spr"
#define MK_CONFIGURE_KEY_KILL_ENGINE "abort"
#define MK_CONFIGURE_KEY_MASTER_VOL "mvol"
#define MK_CONFIGURE_KEY_LOAD_CC_MAP "cm"
#define MK_CONFIGURE_KEY_MIDI_LEARN "ml"
#define MK_CONFIGURE_KEY_ADD_TO_WAV_POOL "wp"
#define MK_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD "wr"
#define MK_CONFIGURE_KEY_LOAD_AB_SET "abs"
#define MK_CONFIGURE_KEY_AUDIO_IN_VOL "aiv"
#define MK_CONFIGURE_KEY_ENGINE "engine"
#define MK_CONFIGURE_KEY_CLEAN_WAV_POOL "cwp"

#define MK_HOST_DAWNEXT 0
#define MK_HOST_WAVENEXT 1


#define MK_HOST_COUNT 2

// 1/128th note resolution, 0.03125f beats
#define MK_AUTOMATION_RESOLUTION (1.0f / 32.0f)
#define ATM_TICK_BUFFER_SIZE 16

volatile int exiting = 0;
float MASTER_VOL __attribute__((aligned(16))) = 1.0f;

float **pluginOutputBuffers;

#ifdef	__cplusplus
extern "C" {
#endif

/* An automation clock event */
typedef struct
{
    /* (int)(song_pos_in_beats / MK_AUTOMATION_RESOLUTION) */
    int tick;
    /* the sample number in the current buffer that the event happens on */
    int sample;
    double beat;
}t_atm_tick;

typedef struct
{
    int sample_count;
    long current_sample;
    double start_beat;
    double end_beat;
    float period_inc_beats;
    float * buffers[2];
    float * sc_buffers[2];
    float * input_buffer;
    int atm_tick_count;
    t_atm_tick atm_ticks[ATM_TICK_BUFFER_SIZE];
}t_sample_period;

typedef struct
{
    int count;
    t_sample_period periods[3];
}t_sample_period_split;

typedef struct
{
    int type;  //0:Loop,1:TempoChange
    double beat;
    double start_beat;  //currently only for the loop event
    float tempo;
}t_mk_seq_event;

typedef struct
{
    int is_looping;
    float tempo;
    float playback_inc;
    float samples_per_beat;
    t_sample_period period;
}t_mk_seq_event_period;

typedef struct
{
    t_sample_period_split splitter;
    int count;
    t_mk_seq_event_period sample_periods[2];
}t_mk_seq_event_result;

typedef struct
{
    int count;
    int pos;
    t_mk_seq_event * events;
    // Each tick of the automation clock happens in this many cycles
    double atm_clock_samples;
    double atm_pos;
    float tempo;
    float playback_inc;
    float samples_per_beat;
    t_sample_period period;
}t_mk_seq_event_list;

typedef struct
{
    char * f_tmp1;
    char * f_tmp2;
    char * f_msg;
    char osc_queue_keys[PYDAW_OSC_SEND_QUEUE_SIZE][12];
    char * osc_queue_vals[PYDAW_OSC_SEND_QUEUE_SIZE];
}t_osc_send_data;

typedef struct
{
    int thread_num;
    int stack_size;
}t_pydaw_thread_args;

typedef struct
{
    /*This is reset to bus_count each cycle and the
     * bus track processed when count reaches 0*/
    volatile int bus_counter;
    char bus_counter_padding[CACHE_LINE_SIZE - sizeof(int)];
    volatile int status;
    char status_padding[CACHE_LINE_SIZE - sizeof(int)];
    t_sample_period_split splitter;
    int solo;
    int mute;
    int period_event_index;
    t_pydaw_plugin * plugins[MAX_PLUGIN_TOTAL_COUNT];
    int track_num;
    t_pkm_peak_meter * peak_meter;
    float ** buffers;
    float ** sc_buffers;
    int sc_buffers_dirty;
    int channels;
    pthread_spinlock_t lock;
    t_ramp_env fade_env;
    int fade_state;
    /*When a note_on event is fired,
     * a sample number of when to release it is stored here*/
    long note_offs[PYDAW_MIDI_NOTE_COUNT];
    int item_event_index;
    char * osc_cursor_message;
    int * extern_midi_count;
    t_midi_device * midi_device;
    t_pydaw_seq_event * extern_midi;
    t_pydaw_seq_event event_buffer[PYDAW_MAX_EVENT_BUFFER_SIZE];
    struct ShdsList * event_list;
}t_pytrack;

typedef struct
{
    void (*run)(int sample_count, float **output, float *a_input_buffers);
    void (*osc_send)(t_osc_send_data*);
    void (*audio_inputs)();
    void (*mix)();
}t_mk_host;

typedef struct
{
    float sample_rate;
    int current_host;
    char padding[CACHE_LINE_SIZE - sizeof(float) - sizeof(int)];
}t_mk_thread_storage __attribute__((aligned(CACHE_LINE_SIZE)));

typedef struct
{
    t_mk_thread_storage thread_storage[MAX_WORKER_THREADS];
    t_mk_host * current_host;
    t_mk_host hosts[MK_HOST_COUNT];
    t_wav_pool * wav_pool;
    float *out;  // From Portaudio's callback
    int sample_count;
    pthread_spinlock_t main_lock;

    //For broadcasting to the threads that it's time to process the tracks
    pthread_cond_t * track_cond;
    //For preventing the main thread from continuing until the workers finish
    pthread_mutex_t * track_block_mutexes;
    pthread_spinlock_t * thread_locks;
    pthread_t * worker_threads;
    int worker_thread_count;
    int * track_thread_quit_notifier;
    void * main_thread_args;

    int is_offline_rendering;
    //set from the audio device buffer size every time the main loop is called.
    t_wav_pool_item * preview_wav_item;
    t_pydaw_audio_item * preview_audio_item;
    float preview_start; //0.0f to 1.0f
    int is_previewing;  //Set this to self->ab_mode on playback
    float preview_amp_lin;
    int preview_max_sample_count;
    t_pyaudio_input * audio_inputs;
    pthread_mutex_t audio_inputs_mutex;
    pthread_t audio_recording_thread;
    int audio_recording_quit_notifier __attribute__((aligned(16)));
    int playback_mode;  //0 == Stop, 1 == Play, 2 == Rec

#ifndef MK_DLL
    lo_server_thread serverThread;
    lo_address uiTarget;
#endif

    char * osc_cursor_message;
    int osc_queue_index;
    char osc_queue_keys[PYDAW_OSC_SEND_QUEUE_SIZE][12];
    char osc_queue_vals[PYDAW_OSC_SEND_QUEUE_SIZE][PYDAW_OSC_MAX_MESSAGE_SIZE];
    pthread_t osc_queue_thread;
    //Threads must hold this to write OSC messages
    pthread_spinlock_t ui_spinlock;
    t_midi_device_list * midi_devices;
    int midi_learn;
    t_pydaw_plugin plugin_pool[MAX_PLUGIN_POOL_COUNT];
    char * project_folder;
    char * audio_folder;
    char * audio_tmp_folder;
    char * samples_folder;
    char * samplegraph_folder;
    char * wav_pool_file;
    char * plugins_folder;
    pthread_mutex_t exit_mutex;
}t_musikernel;

typedef struct
{
    int output_track;
    int on;
}t_pydaw_midi_routing;

#define ROUTE_TYPE_AUDIO 0
#define ROUTE_TYPE_SIDECHAIN 1
#define ROUTE_TYPE_MIDI 2

typedef struct
{
    int output;
    int active;
    int type;
    char padding[4];
}t_pytrack_routing;

void g_musikernel_get(float, t_midi_device_list*);
t_pytrack * g_pytrack_get(int, float);
inline void v_pydaw_zero_buffer(float**, int);
double v_pydaw_print_benchmark(char * a_message,
        struct timespec a_start, struct timespec a_finish);
void * v_pydaw_audio_recording_thread(void* a_arg);
void v_queue_osc_message(char*, char*);
void v_pydaw_set_plugin_index(t_pytrack*, int, int, int, int, int);

t_pytrack_routing * g_pytrack_routing_get();
void v_pytrack_routing_set(t_pytrack_routing *, int, int);
void v_pytrack_routing_free(t_pytrack_routing *);
void v_pydaw_set_host(int);

void v_mk_set_tempo(t_mk_seq_event_list*, float);

#ifdef	__cplusplus
}
#endif

t_musikernel * musikernel = NULL;
int ZERO = 0;

#ifdef MK_DLL

typedef void (*v_ui_send_callback)(char * a_path, char * a_msg);

#if defined(_WIN32)

#warning "You're building for Windows"
void v_set_ui_callback(v_ui_send_callback a_callback);

#endif

typedef void (*v_ui_send_callback)(char * a_path, char * a_msg);

v_ui_send_callback UI_SEND_CALLBACK = NULL;

void v_set_ui_callback(v_ui_send_callback a_callback)
{
    UI_SEND_CALLBACK = a_callback;
}

void v_ui_send(char * a_path, char * a_msg)
{
    UI_SEND_CALLBACK(a_path, a_msg);
}

#else

void v_ui_send(char * a_path, char * a_msg)
{
    lo_send(musikernel->uiTarget, a_path, "s", a_msg);
}

#endif

void v_pytrack_routing_set(t_pytrack_routing * self, int a_output, int a_type)
{
    self->output = a_output;
    self->type = a_type;

    if(a_output >= 0)
    {
        self->active = 1;
    }
    else
    {
        self->active = 0;
    }
}

void v_pytrack_routing_free(t_pytrack_routing * self)
{
    free(self);
}

void v_create_sample_graph(t_wav_pool_item * self)
{
    char str_buff[2048];
    snprintf(str_buff, 2048, "%s/%i",
        musikernel->samplegraph_folder, self->uid);

    if(i_pydaw_file_exists(str_buff))
    {
        return;
    }

    int len;

    FILE * f_sg = fopen(str_buff, "w");

    len = snprintf(str_buff, 2048, "meta|filename|%s\n", self->path);
    fwrite(str_buff, 1, len, f_sg);
    time_t f_ts = time(NULL);

    len = snprintf(str_buff, 2048, "meta|timestamp|%lu\n",
        (unsigned long)f_ts);
    fwrite(str_buff, 1, len, f_sg);

    len = snprintf(str_buff, 2048, "meta|channels|%i\n", self->channels);
    fwrite(str_buff, 1, len, f_sg);

    len = snprintf(str_buff, 2048, "meta|frame_count|%i\n", self->length);
    fwrite(str_buff, 1, len, f_sg);

    len = snprintf(str_buff, 2048, "meta|sample_rate|%i\n",
        (int)self->sample_rate);
    fwrite(str_buff, 1, len, f_sg);

    float f_length = (float)self->length / (float)self->sample_rate;

    len = snprintf(str_buff, 2048, "meta|length|%f\n", f_length);
    fwrite(str_buff, 1, len, f_sg);

    int f_peak_size;

    if(f_length < 3.0)
    {
        f_peak_size = 16;
    }
    else if(f_length < 20.0)
    {
        f_peak_size = (int)((float)self->sample_rate * 0.005);
    }
    else
    {
        f_peak_size = (int)(self->sample_rate * 0.025);
    }

    int f_count = 0;
    int f_i, f_i2, f_i3;
    float f_sample;

    for(f_i2 = 0; f_i2 < self->length; f_i2 += f_peak_size)
    {
        for(f_i = 0; f_i < self->channels; ++f_i)
        {
            float f_high = 0.01;
            float f_low = -0.01;

            int f_stop = f_i2 + f_peak_size;
            if(f_stop > self->length)
                f_stop = self->length;

            for(f_i3 = f_i2; f_i3 < f_stop; ++f_i3)
            {
                f_sample = self->samples[f_i][f_i3];
                if(f_sample > f_high)
                    f_high = f_sample;
                else if(f_sample < f_low)
                    f_low = f_sample;
            }

            len = snprintf(str_buff, 2048, "p|%i|h|%f\n", f_i, f_high);
            fwrite(str_buff, 1, len, f_sg);

            len = snprintf(str_buff, 2048, "p|%i|l|%f\n", f_i, f_low);
            fwrite(str_buff, 1, len, f_sg);
        }
        ++f_count;
    }

    len = snprintf(str_buff, 2048, "meta|count|%i\n", f_count);
    fwrite(str_buff, 1, len, f_sg);

    len = snprintf(str_buff, 2048, "\\");
    fwrite(str_buff, 1, len, f_sg);

    fclose(f_sg);

    snprintf(str_buff, 2048, "%s/%i.finished",
        musikernel->samplegraph_folder, self->uid);
    FILE * f_finished = fopen(str_buff, "w");
    fclose(f_finished);
}


/* default generic t_mk_host->mix function pointer */
void v_default_mix()
{
    register int f_i;
    int framesPerBuffer = musikernel->sample_count;
    float * out = musikernel->out;

    if(OUTPUT_CH_COUNT > 2)
    {
        int f_i2 = 0;
        memset(out, 0,
            sizeof(float) * framesPerBuffer * OUTPUT_CH_COUNT);

        for(f_i = 0; f_i < framesPerBuffer; ++f_i)
        {
            out[f_i2 + MASTER_OUT_L] = pluginOutputBuffers[0][f_i];
            out[f_i2 + MASTER_OUT_R] = pluginOutputBuffers[1][f_i];
            f_i2 += OUTPUT_CH_COUNT;
        }
    }
    else
    {
        for(f_i = 0; f_i < framesPerBuffer; ++f_i)
        {
            *out = pluginOutputBuffers[0][f_i];  // left
            ++out;
            *out = pluginOutputBuffers[1][f_i];  // right
            ++out;
        }
    }
}

void g_sample_period_init(t_sample_period *self)
{
    int f_i;

    self->buffers[0] = NULL;
    self->buffers[1] = NULL;
    self->sc_buffers[0] = NULL;
    self->sc_buffers[1] = NULL;
    self->input_buffer = NULL;
    self->current_sample = 0;
    self->sample_count = 0;
    self->end_beat = 0.0;
    self->start_beat = 0.0;
    self->atm_tick_count = 0;

    for(f_i = 0; f_i < ATM_TICK_BUFFER_SIZE; ++f_i)
    {
        self->atm_ticks[f_i].sample = -1;
        self->atm_ticks[f_i].tick = -1;
        self->atm_ticks[f_i].beat = -99999999999.999999;
    }
}

void g_mk_seq_event_list_init(t_mk_seq_event_list * self)
{
    self->count = 0;
    self->pos = 0;
    self->events = NULL;
    g_sample_period_init(&self->period);
    v_mk_set_tempo(self, 128.0f);
}

void g_seq_event_result_init(t_mk_seq_event_result * self)
{
    self->count = 0;
    int f_i = 0;
    for(f_i = 0; f_i < 2; ++f_i)
    {
        self->sample_periods[f_i].playback_inc = 0.0f;
        self->sample_periods[f_i].samples_per_beat = 0.0f;
        self->sample_periods[f_i].tempo = 0.0f;
        g_sample_period_init(&self->sample_periods[f_i].period);
    }
}

void v_sample_period_split(
        t_sample_period_split* self, float ** a_buffers,
        float ** a_sc_buffers, int a_sample_count,
        double a_period_start_beat, double a_period_end_beat,
        double a_event1_beat, double a_event2_beat, long a_current_sample,
        float * a_input_buffer, int a_input_count)
{
    self->periods[0].current_sample = a_current_sample;

    if(a_event1_beat <= a_period_start_beat ||
    (a_event1_beat >= a_period_end_beat && a_event2_beat >= a_period_end_beat))
    {
        self->count = 1;
        self->periods[0].sample_count = a_sample_count;
        self->periods[0].buffers[0] = a_buffers[0];
        self->periods[0].buffers[1] = a_buffers[1];

        if(a_sc_buffers)
        {
            self->periods[0].sc_buffers[0] = a_sc_buffers[0];
            self->periods[0].sc_buffers[1] = a_sc_buffers[1];
        }

        if(a_input_buffer)
        {
            self->periods[0].input_buffer = a_input_buffer;
        }
    }
    else if(a_event1_beat >= a_period_start_beat &&
            a_event1_beat < a_period_end_beat)
    {
        if(a_event2_beat >= a_period_end_beat)
        {
            self->count = 1;
            self->periods[0].sample_count = a_sample_count;

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_period_end_beat;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers)
            {
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer)
            {
                self->periods[0].input_buffer = a_input_buffer;
            }
        }
        else if(a_event1_beat == a_event2_beat ||
                a_event2_beat >= a_period_end_beat)
        {
            self->count = 2;

            double f_diff = (a_period_end_beat - a_period_start_beat);
            double f_distance = a_event1_beat - a_period_start_beat;
            int f_split =
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_event1_beat;

            self->periods[1].start_beat = a_event1_beat;
            self->periods[1].end_beat = a_period_end_beat;

            self->periods[0].sample_count = f_split;
            self->periods[1].sample_count = a_sample_count - f_split;

            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers)
            {
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer)
            {
                self->periods[0].input_buffer = a_input_buffer;
            }

            self->periods[1].buffers[0] = &a_buffers[0][f_split];
            self->periods[1].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers)
            {
                self->periods[1].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[1].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer)
            {
                self->periods[1].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }
        }
        else if(a_event2_beat < a_period_end_beat)
        {
            self->count = 3;

            double f_diff = (a_period_end_beat - a_period_start_beat);

            double f_distance = a_event1_beat - a_period_start_beat;
            int f_split =
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[0].start_beat = a_period_start_beat;
            self->periods[0].end_beat = a_event1_beat;

            self->periods[1].start_beat = a_event1_beat;
            self->periods[1].end_beat = a_event2_beat;

            self->periods[2].start_beat = a_event2_beat;
            self->periods[2].end_beat = a_period_end_beat;

            self->periods[0].sample_count = f_split;
            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[0].buffers[0] = a_buffers[0];
            self->periods[0].buffers[1] = a_buffers[1];

            if(a_sc_buffers)
            {
                self->periods[0].sc_buffers[0] = a_sc_buffers[0];
                self->periods[0].sc_buffers[1] = a_sc_buffers[1];
            }

            if(a_input_buffer)
            {
                self->periods[0].input_buffer = a_input_buffer;
            }

            f_distance = a_event2_beat - a_event1_beat;
            f_split +=
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            self->periods[1].current_sample = a_current_sample + (long)f_split;

            self->periods[1].sample_count = f_split;
            self->periods[1].buffers[0] = &a_buffers[0][f_split];
            self->periods[1].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers)
            {
                self->periods[1].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[1].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer)
            {
                self->periods[1].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }

            f_distance = a_period_end_beat - a_event2_beat;
            f_split +=
                (int)((f_distance / f_diff) * ((double)(a_sample_count)));

            f_split = a_sample_count - f_split;
            self->periods[2].sample_count = f_split;
            self->periods[2].buffers[0] = &a_buffers[0][f_split];
            self->periods[2].buffers[1] = &a_buffers[1][f_split];

            if(a_sc_buffers)
            {
                self->periods[2].sc_buffers[0] = &a_sc_buffers[0][f_split];
                self->periods[2].sc_buffers[1] = &a_sc_buffers[1][f_split];
            }

            if(a_input_buffer)
            {
                self->periods[2].input_buffer =
                    &a_input_buffer[f_split * a_input_count];
            }
        }
        else
        {
            assert(0);
        }
    }
    else
    {
        assert(0);
    }
}

void pydaw_osc_error(int num, const char *msg, const char *path)
{
    fprintf(stderr, "PyDAW: liblo server error %d in path %s: %s\n",
	    num, path, msg);
}

void g_musikernel_get(float a_sr, t_midi_device_list * a_midi_devices)
{
    clalloc((void**)&musikernel, sizeof(t_musikernel));
    musikernel->wav_pool = g_wav_pool_get(a_sr);
    musikernel->midi_devices = a_midi_devices;
    musikernel->current_host = NULL;
    musikernel->sample_count = 512;
    musikernel->midi_learn = 0;
    musikernel->is_offline_rendering = 0;
    pthread_spin_init(&musikernel->main_lock, 0);
    musikernel->project_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_tmp_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->samples_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->samplegraph_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->wav_pool_file = (char*)malloc(sizeof(char) * 1024);
    musikernel->plugins_folder = (char*)malloc(sizeof(char) * 1024);

    musikernel->preview_wav_item = 0;
    musikernel->preview_audio_item = g_pydaw_audio_item_get(a_sr);
    musikernel->preview_start = 0.0f;
    musikernel->preview_amp_lin = 1.0f;
    musikernel->is_previewing = 0;
    musikernel->preview_max_sample_count = ((int)(a_sr)) * 30;
    musikernel->playback_mode = 0;

    pthread_mutex_init(&musikernel->audio_inputs_mutex, NULL);
    pthread_mutex_init(&musikernel->exit_mutex, NULL);

    int f_i;

    hpalloc((void**)&musikernel->audio_inputs,
        sizeof(t_pyaudio_input) * PYDAW_AUDIO_INPUT_TRACK_COUNT);

    for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        g_pyaudio_input_init(&musikernel->audio_inputs[f_i], a_sr);
    }

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i)
    {
        musikernel->thread_storage[f_i].sample_rate = a_sr;
        musikernel->thread_storage[f_i].current_host = MK_HOST_DAWNEXT;
    }

    /* Create OSC thread */

    pthread_spin_init(&musikernel->ui_spinlock, 0);
    musikernel->osc_queue_index = 0;
    musikernel->osc_cursor_message = (char*)malloc(sizeof(char) * 1024);

#ifndef MK_DLL
    musikernel->serverThread = lo_server_thread_new(NULL, pydaw_osc_error);
    musikernel->uiTarget = lo_address_new_from_url(
        "osc.udp://localhost:30321/");
#endif

    for(f_i = 0; f_i < MAX_PLUGIN_POOL_COUNT; ++f_i)
    {
        musikernel->plugin_pool[f_i].active = 0;
    }
}

void v_pydaw_set_control_from_atm(t_pydaw_seq_event *event,
        int a_plugin_uid, t_pytrack * f_track)
{
    if(!musikernel->is_offline_rendering)
    {
        sprintf(
            f_track->osc_cursor_message, "%i|%i|%f",
            a_plugin_uid, event->port, event->value);
        v_queue_osc_message("pc", f_track->osc_cursor_message);
    }
}

void v_pydaw_set_control_from_cc(t_pydaw_seq_event *event, t_pytrack * f_track)
{
    if(!musikernel->is_offline_rendering)
    {
        sprintf(
            f_track->osc_cursor_message, "%i|%i|%i",
            f_track->track_num, event->param, (int)(event->value));
        v_queue_osc_message("cc", f_track->osc_cursor_message);
    }
}

void v_queue_osc_message(
    char * __restrict__ a_key, char * __restrict__ a_val)
{
    if(musikernel->osc_queue_index >= PYDAW_OSC_SEND_QUEUE_SIZE)
    {
        printf("Dropping OSC event to prevent buffer overrun:\n%s|%s\n\n",
                a_key, a_val);
    }
    else
    {
        pthread_spin_lock(&musikernel->ui_spinlock);
        sprintf(musikernel->osc_queue_keys[musikernel->osc_queue_index],
                "%s", a_key);
        sprintf(musikernel->osc_queue_vals[musikernel->osc_queue_index],
                "%s", a_val);
        ++musikernel->osc_queue_index;
        pthread_spin_unlock(&musikernel->ui_spinlock);
    }
}

void v_pydaw_set_host(int a_mode)
{
    int f_i;

    assert(a_mode >= 0 && a_mode < MK_HOST_COUNT);

    pthread_spin_lock(&musikernel->main_lock);

    musikernel->current_host = &musikernel->hosts[a_mode];

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i)
    {
        musikernel->thread_storage[f_i].current_host = a_mode;
    }

#ifndef NO_MIDI

    t_midi_device * f_device;

    if(musikernel->midi_devices)
    {
        for(f_i = 0; f_i < musikernel->midi_devices->count; ++f_i)
        {
            f_device = &musikernel->midi_devices->devices[f_i];
            if(f_device->loaded)
            {
                midiPoll(f_device);
                f_device->midiEventReadIndex = f_device->midiEventWriteIndex;
            }

        }
    }
#endif

    pthread_spin_unlock(&musikernel->main_lock);

    if(musikernel->current_host->audio_inputs)
    {
        musikernel->current_host->audio_inputs();
    }
}

#ifndef MK_DLL
void v_pydaw_activate_osc_thread(lo_method_handler osc_message_handler)
{
    lo_server_thread_add_method(musikernel->serverThread, NULL, NULL,
            osc_message_handler, NULL);
    lo_server_thread_start(musikernel->serverThread);
}
#endif

#ifdef __linux__
/* Create a clock_t with clock() when beginning some work,
 * and use this function to print the completion time*/
inline double v_pydaw_print_benchmark(char * a_message,
    struct timespec f_start, struct timespec f_finish)
{
    double elapsed;
    elapsed = (f_finish.tv_sec - f_start.tv_sec);
    elapsed += (f_finish.tv_nsec - f_start.tv_nsec) / 1000000000.0;

    printf ( "\n\nCompleted %s in %lf seconds\n", a_message, elapsed);

    return elapsed;
}
#endif

inline void v_pydaw_zero_buffer(float ** a_buffers, int a_count)
{
    register int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffers[0][f_i2] = 0.0f;
        a_buffers[1][f_i2] = 0.0f;
        ++f_i2;
    }
}

void v_pydaw_open_track(t_pytrack * a_track, char * a_tracks_folder,
        int a_index)
{
    char f_file_name[1024];

    sprintf(f_file_name, "%s%s%i", a_tracks_folder, PATH_SEP, a_index);

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

            if(f_2d_array->current_str[0] == 'p')  //plugin
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_uid = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array); //mute
                v_iterate_2d_char_array(f_2d_array); //solo
                v_iterate_2d_char_array(f_2d_array);
                int f_power = atoi(f_2d_array->current_str);

                v_pydaw_set_plugin_index(a_track, f_index, f_plugin_index,
                    f_plugin_uid, f_power, 0);

            }
            else
            {
                printf("Invalid track identifier '%c'\n",
                    f_2d_array->current_str[0]);
                assert(0);
            }
        }

        g_free_2d_char_array(f_2d_array);
    }
    else
    {
        int f_i;
        for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i)
        {
            v_pydaw_set_plugin_index(a_track, f_i, 0, -1, 0, 0);
        }
    }
}

t_pytrack * g_pytrack_get(int a_track_num, float a_sr)
{
    int f_i = 0;

    t_pytrack * f_result;
    clalloc((void**)&f_result, sizeof(t_pytrack));

    f_result->track_num = a_track_num;
    f_result->channels = 2;
    f_result->extern_midi = 0;
    f_result->extern_midi_count = &ZERO;
    f_result->midi_device = 0;
    f_result->sc_buffers_dirty = 0;
    f_result->event_list = shds_list_new(PYDAW_MAX_EVENT_BUFFER_SIZE, NULL);

    pthread_spin_init(&f_result->lock, 0);

    hpalloc((void**)&f_result->buffers, (sizeof(float*) * f_result->channels));
    hpalloc((void**)&f_result->sc_buffers,
        (sizeof(float*) * f_result->channels));

    while(f_i < f_result->channels)
    {
        clalloc((void**)&f_result->buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        clalloc((void**)&f_result->sc_buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        ++f_i;
    }

    v_pydaw_zero_buffer(f_result->buffers, FRAMES_PER_BUFFER);
    v_pydaw_zero_buffer(f_result->sc_buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;

    f_result->bus_counter = 0;

    f_i = 0;

    while(f_i < PYDAW_MAX_EVENT_BUFFER_SIZE)
    {
        v_pydaw_ev_clear(&f_result->event_buffer[f_i]);
        ++f_i;
    }

    f_i = 0;
    while(f_i < MAX_PLUGIN_TOTAL_COUNT)
    {
        f_result->plugins[f_i] = NULL;
        ++f_i;
    }

    f_i = 0;

    while(f_i < PYDAW_MIDI_NOTE_COUNT)
    {
        f_result->note_offs[f_i] = -1;
        ++f_i;
    }

    f_result->period_event_index = 0;

    f_result->peak_meter = g_pkm_get();

    g_rmp_init(&f_result->fade_env, a_sr);
    v_rmp_set_time(&f_result->fade_env, 0.03f);
    f_result->fade_state = 0;

    hpalloc((void**)&f_result->osc_cursor_message, sizeof(char) * 1024);

    f_result->status = STATUS_NOT_PROCESSED;

    return f_result;
}

void v_pydaw_set_preview_file(const char * a_file)
{
    t_wav_pool_item * f_result = g_wav_pool_item_get(0, a_file,
            musikernel->thread_storage[0].sample_rate);

    if(f_result)
    {
        if(i_wav_pool_item_load(f_result, 0))
        {
            t_wav_pool_item * f_old = musikernel->preview_wav_item;

            pthread_spin_lock(&musikernel->main_lock);

            musikernel->preview_wav_item = f_result;

            musikernel->preview_audio_item->ratio =
                    musikernel->preview_wav_item->ratio_orig;

            musikernel->is_previewing = 1;

            v_ifh_retrigger(
                &musikernel->preview_audio_item->sample_read_heads[0],
                PYDAW_AUDIO_ITEM_PADDING_DIV2);
            v_adsr_retrigger(&musikernel->preview_audio_item->adsrs[0]);

            pthread_spin_unlock(&musikernel->main_lock);

            if(f_old)
            {
                v_wav_pool_item_free(f_old);
            }
        }
        else
        {
            printf("i_wav_pool_item_load(f_result) failed in "
                    "v_pydaw_set_preview_file\n");
        }
    }
    else
    {
        musikernel->is_previewing = 0;
        printf("g_wav_pool_item_get returned zero. could not load "
                "preview item.\n");
    }
}

void v_prepare_to_record_audio()
{
    int f_i;
    t_pyaudio_input * f_ai;

    pthread_mutex_lock(&musikernel->audio_inputs_mutex);

    for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        f_ai = &musikernel->audio_inputs[f_i];

        f_ai->current_buffer = 0;
        f_ai->flush_last_buffer_pending = 0;
        f_ai->buffer_iterator[0] = 0;
        f_ai->buffer_iterator[1] = 0;
    }

    pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
}

void v_stop_record_audio()
{
    int f_i, f_frames, f_count;
    t_pyaudio_input * f_ai;
    char f_file_name_old[2048];
    char f_file_name_new[2048];

    pthread_mutex_lock(&musikernel->exit_mutex);
    printf("Stopping recording, shutdown is inhibited.\n");
    pthread_mutex_lock(&musikernel->audio_inputs_mutex);

    for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        f_ai = &musikernel->audio_inputs[f_i];
        if(f_ai->rec)
        {
            f_frames = f_ai->buffer_iterator[(f_ai->current_buffer)]
                / f_ai->channels;

            if(f_frames)
            {
                f_count =sf_writef_float(f_ai->sndfile,
                    f_ai->rec_buffers[(f_ai->current_buffer)],
                    ((f_ai->buffer_iterator[(f_ai->current_buffer)])
                    / f_ai->channels));

                printf("sf_writef_float returned %i\n", f_count);
            }

            sf_close(f_ai->sndfile);
            f_ai->sndfile = NULL;

            sprintf(f_file_name_old, "%s%i",
                musikernel->audio_tmp_folder, f_i);

            sprintf(f_file_name_new, "%s%i.wav",
                musikernel->audio_tmp_folder, f_i);

            rename(f_file_name_old, f_file_name_new);

            v_pydaw_audio_input_record_set(
                &musikernel->audio_inputs[f_i], f_file_name_old);
        }
    }

    pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
    pthread_mutex_unlock(&musikernel->exit_mutex);
    printf("Finished stopping recording, shutdown is no longer inhibited.\n");
}

void * v_pydaw_audio_recording_thread(void* a_arg)
{
    t_pyaudio_input * f_ai;
    int f_count;
    int f_i;
    int f_frames;

    sleep(3);

    while(1)
    {
        int f_did_something = 0;

        pthread_mutex_lock(&musikernel->audio_inputs_mutex);

        if(musikernel->audio_recording_quit_notifier)
        {
            pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
            printf("audio recording thread exiting...\n");
            break;
        }

        if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
        {
            for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
            {
                f_ai = &musikernel->audio_inputs[f_i];
                if((f_ai->rec) && (f_ai->flush_last_buffer_pending))
                {
                    f_frames = f_ai->buffer_iterator[(f_ai->buffer_to_flush)]
                        / f_ai->channels;
                    f_did_something = 1;

                    assert(f_ai->channels == f_ai->sf_info.channels);

                    printf("Flushing record buffer of "
                        "%i frames, %i channels for input %i\n",
                        f_frames, f_ai->channels, f_i);

                    f_count = sf_writef_float(f_ai->sndfile,
                        f_ai->rec_buffers[f_ai->buffer_to_flush], f_frames);

                    printf("sf_writef_float returned %i\n", f_count);

                    f_ai->flush_last_buffer_pending = 0;
                    f_ai->buffer_iterator[f_ai->buffer_to_flush] = 0;
                }
            }
        }

        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);

        if(!f_did_something)
        {
            usleep(10000);
        }
    }

    return (void*)1;
}

void v_audio_input_run(int f_index, float ** output, float ** sc_output,
        float * a_input, int sample_count, int * a_sc_dirty)
{
    int f_i2;
    float f_tmp_sample;
    t_pyaudio_input * f_ai = &musikernel->audio_inputs[f_index];

    int f_output_mode = f_ai->output_mode;

    if(f_output_mode)
    {
        *a_sc_dirty = 1;
    }

    if(f_ai->rec && musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
    {
        int f_buffer_pos = f_index;

        if(((f_ai->buffer_iterator[(f_ai->current_buffer)])
                + (sample_count * f_ai->channels) ) >=
                PYDAW_AUDIO_INPUT_REC_BUFFER_SIZE)
        {
            f_ai->buffer_to_flush = (f_ai->current_buffer);
            f_ai->flush_last_buffer_pending = 1;

            if((f_ai->current_buffer) == 0)
            {
                f_ai->current_buffer = 1;
            }
            else
            {
                f_ai->current_buffer = 0;
            }
        }

        int f_current_buffer = (f_ai->current_buffer);
        int f_orig_buffer_pos = f_ai->buffer_iterator[f_current_buffer];

        for(f_i2 = 0; f_i2 < sample_count; ++f_i2)
        {
            f_tmp_sample = a_input[f_buffer_pos] * (f_ai->vol_linear);

            f_ai->rec_buffers[f_current_buffer][
                f_ai->buffer_iterator[f_current_buffer]] = f_tmp_sample;
            f_ai->buffer_iterator[f_current_buffer] += f_ai->channels;

            f_buffer_pos += PYDAW_AUDIO_INPUT_TRACK_COUNT;
        }

        if(f_ai->stereo_ch >= 0)
        {
            f_buffer_pos = f_ai->stereo_ch;
            f_ai->buffer_iterator[f_current_buffer] = f_orig_buffer_pos + 1;

            for(f_i2 = 0; f_i2 < sample_count; ++f_i2)
            {
                f_tmp_sample = a_input[f_buffer_pos] * (f_ai->vol_linear);

                f_ai->rec_buffers[f_current_buffer][
                    f_ai->buffer_iterator[f_current_buffer]] = f_tmp_sample;
                f_ai->buffer_iterator[f_current_buffer] += f_ai->channels;

                f_buffer_pos += PYDAW_AUDIO_INPUT_TRACK_COUNT;
            }

            // Move it back to the correct position
            --f_ai->buffer_iterator[f_current_buffer];
        }
    }

    if(f_ai->monitor)
    {
        int f_buffer_pos = f_index;

        for(f_i2 = 0; f_i2 < sample_count; ++f_i2)
        {
            f_tmp_sample = a_input[f_buffer_pos] * (f_ai->vol_linear);

            if(f_output_mode != 1)
            {
                output[0][f_i2] += f_tmp_sample;
            }

            if(f_output_mode > 0)
            {
                sc_output[0][f_i2] += f_tmp_sample;
            }

            if(f_ai->stereo_ch == -1)
            {
                if(f_output_mode != 1)
                {
                    output[1][f_i2] += f_tmp_sample;
                }

                if(f_output_mode > 0)
                {
                    sc_output[1][f_i2] += f_tmp_sample;
                }
            }

            f_buffer_pos += PYDAW_AUDIO_INPUT_TRACK_COUNT;
        }

        if(f_ai->stereo_ch >= 0)
        {
            f_buffer_pos = f_ai->stereo_ch;

            for(f_i2 = 0; f_i2 < sample_count; ++f_i2)
            {
                f_tmp_sample = a_input[f_buffer_pos] * (f_ai->vol_linear);

                if(f_output_mode != 1)
                {
                    output[1][f_i2] += f_tmp_sample;
                }

                if(f_output_mode > 0)
                {
                    sc_output[1][f_i2] += f_tmp_sample;
                }

                f_buffer_pos += PYDAW_AUDIO_INPUT_TRACK_COUNT;
            }
        }
    }
}

void v_pydaw_update_audio_inputs(char * a_project_folder)
{
    char f_inputs_file[2048];
    char f_tmp_file_name[2048];

    t_pyaudio_input * f_ai;
    sprintf(f_inputs_file, "%s%sinput.txt", a_project_folder, PATH_SEP);

    if(a_project_folder && i_pydaw_file_exists(f_inputs_file))
    {
        int f_i;
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
            f_inputs_file, PYDAW_LARGE_STRING);

        pthread_mutex_lock(&musikernel->audio_inputs_mutex);

        for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof) //!strcmp(f_index_str, "\\"))
            {
                break;
            }

            int f_index = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_rec = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_monitor = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_vol = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_out = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_right_ch = atoi(f_2d_array->current_str);

            if(f_right_ch >= PYDAW_AUDIO_INPUT_TRACK_COUNT)
            {
                f_right_ch = -1;
            }

            v_iterate_2d_char_array(f_2d_array);
            int f_output_mode = atoi(f_2d_array->current_str);

            // name, ignored by the engine
            v_iterate_2d_char_array_to_next_line(f_2d_array);

            if(f_index >= PYDAW_AUDIO_INPUT_TRACK_COUNT)
            {
                continue;
            }

            f_ai = &musikernel->audio_inputs[f_index];
            f_ai->rec = f_rec;
            f_ai->monitor = f_monitor;
            f_ai->output_track = f_out;
            f_ai->output_mode = f_output_mode;
            f_ai->stereo_ch = f_right_ch;
            f_ai->vol = f_vol;
            f_ai->vol_linear = f_db_to_linear_fast(f_vol);

            sprintf(f_tmp_file_name, "%s%i",
                musikernel->audio_tmp_folder, f_index);

            v_pydaw_audio_input_record_set(f_ai, f_tmp_file_name);
        }

        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
        g_free_2d_char_array(f_2d_array);
    }
    else
    {
        printf("%s not found, setting default values\n", f_inputs_file);
        pthread_mutex_lock(&musikernel->audio_inputs_mutex);
        int f_i;
        for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            f_ai = &musikernel->audio_inputs[f_i];
            f_ai->rec = 0;
            f_ai->monitor = 0;
            f_ai->output_track = 0;
            f_ai->output_track = 0;
            f_ai->stereo_ch = -1;

            f_ai->vol = 0.0f;
            f_ai->vol_linear = 1.0f;

            sprintf(f_tmp_file_name, "%s%i",
                musikernel->audio_tmp_folder, f_i);

            v_pydaw_audio_input_record_set(f_ai, f_tmp_file_name);
        }
        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
    }
}

inline double f_bpm_to_seconds_per_beat(double a_tempo)
{
    return (60.0f / a_tempo);
}

inline double f_pydaw_samples_to_beat_count(int a_sample_count, double a_tempo,
        float a_sr)
{
    double f_seconds_per_beat = f_bpm_to_seconds_per_beat(a_tempo);
    double f_seconds = (double)(a_sample_count) / a_sr;
    return f_seconds / f_seconds_per_beat;
}

inline int i_beat_count_to_samples(double a_beat_count, float a_tempo,
        float a_sr)
{
    double f_seconds = f_bpm_to_seconds_per_beat(a_tempo) * a_beat_count;
    return (int)(f_seconds * a_sr);
}


inline void v_buffer_mix(int a_count,
    float ** __restrict__ a_buffer_src, float ** __restrict__ a_buffer_dest)
{
    register int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffer_dest[0][f_i2] += a_buffer_src[0][f_i2];
        a_buffer_dest[1][f_i2] += a_buffer_src[1][f_i2];
        ++f_i2;
    }
}

void v_wait_for_threads()
{
    int f_i;

    for(f_i = 1; f_i < (musikernel->worker_thread_count); ++f_i)
    {
        pthread_spin_lock(&musikernel->thread_locks[f_i]);
        pthread_spin_unlock(&musikernel->thread_locks[f_i]);
    }
}

void g_pynote_init(t_pydaw_seq_event * f_result, int a_note, int a_vel,
        float a_start, float a_length)
{
    f_result->type = PYDAW_EVENT_NOTEON;
    f_result->length = a_length;
    f_result->note = a_note;
    f_result->start = a_start;
    f_result->velocity = a_vel;
}

t_pydaw_seq_event * g_pynote_get(int a_note, int a_vel,
        float a_start, float a_length)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pynote_init(f_result, a_note, a_vel, a_start, a_length);
    return f_result;
}

void g_pycc_init(t_pydaw_seq_event * f_result, int a_cc_num,
    float a_cc_val, float a_start)
{
    f_result->type = PYDAW_EVENT_CONTROLLER;
    f_result->param = a_cc_num;
    f_result->value = a_cc_val;
    f_result->start = a_start;
}

t_pydaw_seq_event * g_pycc_get(int a_cc_num, float a_cc_val, float a_start)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pycc_init(f_result, a_cc_num, a_cc_val, a_start);
    return f_result;
}

void g_pypitchbend_init(t_pydaw_seq_event * f_result, float a_start,
    float a_value)
{
    f_result->type = PYDAW_EVENT_PITCHBEND;
    f_result->start = a_start;
    f_result->value = a_value;
}

t_pydaw_seq_event * g_pypitchbend_get(float a_start, float a_value)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pypitchbend_init(f_result, a_start, a_value);
    return f_result;
}

void v_sample_period_set_atm_events(t_sample_period * self,
    t_mk_seq_event_list * a_event_list, long a_current_sample,
    int a_sample_count)
{
    double pos;
    double current_sample = (double)(a_current_sample);
    double next_sample = (double)(a_current_sample + (long)a_sample_count);
    self->atm_tick_count = 0;

    for(;
        a_event_list->atm_pos < next_sample;
        a_event_list->atm_pos += a_event_list->atm_clock_samples)
    {
        assert(self->atm_tick_count < ATM_TICK_BUFFER_SIZE);

        pos = (a_event_list->atm_pos - current_sample);
        self->atm_ticks[self->atm_tick_count].sample = (int)(pos);

        self->atm_ticks[self->atm_tick_count].beat =
            self->start_beat +
            f_pydaw_samples_to_beat_count(
                self->atm_ticks[self->atm_tick_count].sample + 1, // round up
                a_event_list->tempo,
                musikernel->thread_storage[0].sample_rate);
        // BUG:  This doesn't quite line up... the result can be off by one
        self->atm_ticks[self->atm_tick_count].tick =
            (int)((self->atm_ticks[self->atm_tick_count].beat /
                MK_AUTOMATION_RESOLUTION) + 0.5f);

        ++self->atm_tick_count;
    }
}

void v_mk_set_time_params(t_sample_period * self)
{
    self->start_beat = self->end_beat;
    self->end_beat = self->start_beat + self->period_inc_beats;
}

void v_mk_seq_event_result_set_default(t_mk_seq_event_result * self,
        t_mk_seq_event_list * a_list,
        float ** a_buffers, float * a_input_buffers, int a_input_count,
        int a_sample_count, long a_current_sample)
{
    self->count = 1;
    t_sample_period * f_period = &self->sample_periods[0].period;
    f_period->period_inc_beats =
        ((a_list->playback_inc) * ((float)(a_sample_count)));
    v_mk_set_time_params(f_period);
    f_period->current_sample = a_current_sample;
    f_period->sample_count = a_sample_count;
    f_period->buffers[0] = a_buffers[0];
    f_period->buffers[1] = a_buffers[1];
    f_period->input_buffer = a_input_buffers;
}

void v_set_sample_period(t_sample_period * self, float a_playback_inc,
        float ** a_buffers, float ** a_sc_buffers, float * a_input_buffers,
        int a_sample_count, long a_current_sample)
{
    self->period_inc_beats = a_playback_inc * ((float)(a_sample_count));

    self->current_sample = a_current_sample;
    self->sample_count = a_sample_count;

    if(a_sc_buffers)
    {
        self->sc_buffers[0] = a_sc_buffers[0];
        self->sc_buffers[1] = a_sc_buffers[1];
    }
    else
    {
        self->sc_buffers[0] = NULL;
        self->sc_buffers[1] = NULL;
    }

    self->buffers[0] = a_buffers[0];
    self->buffers[1] = a_buffers[1];
    self->input_buffer = a_input_buffers;
}

void v_mk_set_tempo(t_mk_seq_event_list * self, float a_tempo)
{
    float f_sample_rate = musikernel->thread_storage[0].sample_rate;
    self->tempo = a_tempo;
    self->playback_inc = (1.0f / f_sample_rate) / (60.0f / a_tempo);
    self->samples_per_beat = (f_sample_rate) / (a_tempo / 60.0f);
    self->atm_clock_samples = self->samples_per_beat * MK_AUTOMATION_RESOLUTION;
}

void v_mk_set_playback_pos(
        t_mk_seq_event_list * self, double a_beat, long a_current_sample)
{
    t_mk_seq_event * f_ev;
    self->period.start_beat = a_beat;
    self->period.end_beat = a_beat;
    self->atm_pos = (double)a_current_sample;
    int f_found_tempo = 0;
    int f_i;
    self->pos = 0;

    for(f_i = 0; f_i < self->count; ++f_i)
    {
         f_ev = &self->events[f_i];

         if(f_ev->beat > a_beat)
         {
             break;
         }

         if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE)
         {
             v_mk_set_tempo(self, f_ev->tempo);
             f_found_tempo = 1;
         }
    }

    assert(f_found_tempo);
}


void v_mk_seq_event_list_set(t_mk_seq_event_list * self,
        t_mk_seq_event_result * a_result,
        float ** a_buffers, float * a_input_buffers, int a_input_count,
        int a_sample_count, long a_current_sample, int a_loop_mode)
{
    int f_i;
    for(f_i = 0; f_i < 2; ++f_i)
    {
        a_result->sample_periods[f_i].is_looping = 0;
        a_result->sample_periods[f_i].tempo = self->tempo;
    }

    if(self->pos >= self->count)
    {
        v_mk_seq_event_result_set_default(a_result, self,
            a_buffers, a_input_buffers, a_input_count,
            a_sample_count, a_current_sample);
    }
    else
    {
        a_result->count = 0;

        double f_loop_start = -1.0f;

        t_mk_seq_event * f_ev = NULL;
        //The scratchpad sample period for iterating
        t_sample_period * f_tmp_period = NULL;
        //temp variable for the outputted sample period
        t_mk_seq_event_period * f_period = NULL;

        v_set_sample_period(&self->period, self->playback_inc,
            a_buffers, NULL, a_input_buffers,
            a_sample_count, a_current_sample);

        v_mk_set_time_params(&self->period);

        while(1)
        {
            if(self->pos >= self->count)
            {
                break;
            }
            else if(self->events[self->pos].beat >= self->period.start_beat &&
                    self->events[self->pos].beat < self->period.end_beat)
            {
                if(self->events[self->pos].beat == self->period.start_beat)
                {
                    a_result->count = 1;
                }
                else
                {
                    a_result->count = 2;
                }

                f_ev = &self->events[self->pos];
                //The period that is returned to the main loop

                if(f_ev->type == SEQ_EVENT_LOOP && a_loop_mode)
                {
                    f_loop_start = f_ev->start_beat;
                    f_period = &a_result->sample_periods[a_result->count - 1];
                    f_period->is_looping = 1;
                }
                else if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE)
                {
                    if(a_result->count == 2)
                    {
                        f_period = &a_result->sample_periods[0];

                        f_period->tempo = self->tempo;
                        f_period->playback_inc = self->playback_inc;
                        f_period->samples_per_beat = self->samples_per_beat;
                    }

                    v_mk_set_tempo(self, f_ev->tempo);

                    f_period = &a_result->sample_periods[a_result->count - 1];

                    f_period->tempo = self->tempo;
                    f_period->playback_inc = self->playback_inc;
                    f_period->samples_per_beat = self->samples_per_beat;
                }
                ++self->pos;
            }
            else if(self->events[self->pos].beat < self->period.start_beat)
            {
                f_ev = &self->events[self->pos];

                if(f_ev->type == SEQ_EVENT_TEMPO_CHANGE)
                {
                    v_mk_set_tempo(self, f_ev->tempo);
                }

                ++self->pos;
            }
            else
            {
                break;
            }
        }

        if(a_result->count == 0)
        {
            a_result->count = 1;

            f_period = &a_result->sample_periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                a_buffers, NULL, a_input_buffers,
                a_sample_count, a_current_sample);

            f_period->tempo = self->tempo;
            f_period->playback_inc = self->playback_inc;
            f_period->samples_per_beat = self->samples_per_beat;

            f_period->period.start_beat = self->period.start_beat;
            f_period->period.end_beat = self->period.end_beat;
        }
        else if(a_result->count == 1)
        {
            f_tmp_period = &self->period;
            f_period = &a_result->sample_periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                f_tmp_period->buffers, NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample);

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((float)(f_tmp_period->sample_count)));

            if(f_loop_start >= 0.0)
            {
                self->pos = 0;
                f_period->period.start_beat = f_loop_start;
            }
            else
            {
                f_period->period.start_beat = f_tmp_period->start_beat;
            }

            f_period->period.end_beat = f_period->period.start_beat +
                f_period->period.period_inc_beats;
            self->period.end_beat = f_period->period.end_beat;
        }
        else if(a_result->count == 2)
        {
            f_period = &a_result->sample_periods[0];

            v_sample_period_split(
                &a_result->splitter, self->period.buffers, NULL,
                self->period.sample_count,
                self->period.start_beat,
                self->period.end_beat,
                f_ev->beat, f_ev->beat,
                self->period.current_sample,
                self->period.input_buffer, a_input_count);

            f_tmp_period = &a_result->splitter.periods[0];

            v_set_sample_period(&f_period->period, self->playback_inc,
                f_tmp_period->buffers, NULL,
                f_tmp_period->input_buffer,
                f_tmp_period->sample_count,
                f_tmp_period->current_sample);

            f_period->period.period_inc_beats = ((f_period->playback_inc) *
                ((float)(f_tmp_period->sample_count)));

            f_period->period.start_beat = f_tmp_period->start_beat;

            f_period->period.end_beat = f_tmp_period->end_beat;

            if(a_result->splitter.count == 2)
            {
                f_period = &a_result->sample_periods[1];
                f_tmp_period = &a_result->splitter.periods[1];

                v_set_sample_period(
                    &f_period->period, self->playback_inc,
                    f_tmp_period->buffers, NULL,
                    f_tmp_period->input_buffer,
                    f_tmp_period->sample_count,
                    f_tmp_period->current_sample);

                if(f_loop_start >= 0.0)
                {
                    self->pos = 0;
                    f_period->period.start_beat = f_loop_start;
                }
                else
                {
                    f_period->period.start_beat = f_tmp_period->start_beat;
                }

                f_period->period.period_inc_beats = ((f_period->playback_inc) *
                    ((float)(f_tmp_period->sample_count)));
                f_period->period.end_beat = f_period->period.start_beat +
                    f_period->period.period_inc_beats;
            }
            else if(a_result->splitter.count == 1)
            {
                // TODO:  Debug how and why this happens
            }
            else
            {
                assert(0);
            }

            self->period.end_beat = f_period->period.end_beat;
        }
        else
        {
            assert(0);
        }
    }
}


void v_mk_configure(const char* a_key, const char* a_value)
{
    printf("v_mk_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, MK_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 3,
                PYDAW_TINY_STRING);

        int f_plugin_uid = atoi(f_val_arr->array[0]);

        int f_port = atoi(f_val_arr->array[1]);
        float f_value = atof(f_val_arr->array[2]);

        t_pydaw_plugin * f_instance;
        pthread_spin_lock(&musikernel->main_lock);

        f_instance = &musikernel->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->set_port_value(
                f_instance->PYFX_handle, f_port, f_value);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }
        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_CONFIGURE_PLUGIN))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 3,
                PYDAW_LARGE_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        char * f_key = f_val_arr->array[1];
        char * f_message = f_val_arr->array[2];

        t_pydaw_plugin * f_instance = &musikernel->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->configure(
                f_instance->PYFX_handle, f_key, f_message,
                &musikernel->main_lock);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_MASTER_VOL))
    {
        MASTER_VOL = atof(a_value);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_AUDIO_IN_VOL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_index = atoi(f_val_arr->array[0]);
        float f_vol = atof(f_val_arr->array[1]);
        float f_vol_linear = f_db_to_linear_fast(f_vol);

        g_free_1d_char_array(f_val_arr);

        t_pyaudio_input * f_input = &musikernel->audio_inputs[f_index];

        f_input->vol = f_vol;
        f_input->vol_linear = f_vol_linear;
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_KILL_ENGINE))
    {
        pthread_spin_lock(&musikernel->main_lock);
        assert(0);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_EXIT))
    {
        pthread_mutex_lock(&musikernel->exit_mutex);
        exiting = 1;
        pthread_mutex_unlock(&musikernel->exit_mutex);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_LOAD_CC_MAP))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        musikernel->plugin_pool[f_plugin_uid].descriptor->set_cc_map(
            musikernel->plugin_pool[f_plugin_uid].PYFX_handle,
            f_val_arr->array[1]);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_MIDI_LEARN))
    {
        musikernel->midi_learn = 1;
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_ADD_TO_WAV_POOL))
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        printf("v_wav_pool_add_item(musikernel->wav_pool, %i, \"%s\")\n",
                atoi(f_kvp->key), f_kvp->value);
        t_wav_pool_item * result =
            v_wav_pool_add_item(musikernel->wav_pool,
                atoi(f_kvp->key), f_kvp->value);
        i_wav_pool_item_load(result, 1);
        v_create_sample_graph(result);
        free(f_kvp);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_PREVIEW_SAMPLE))
    {
        v_pydaw_set_preview_file(a_value);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_STOP_PREVIEW))
    {
        if(musikernel->is_previewing)
        {
            pthread_spin_lock(&musikernel->main_lock);
            v_adsr_release(&musikernel->preview_audio_item->adsrs[0]);
            pthread_spin_unlock(&musikernel->main_lock);
        }
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_RATE_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_end = atof(f_arr->current_str);

        v_pydaw_rate_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_LOAD_AB_SET))
    {
        int f_mode = atoi(a_value);
        v_pydaw_set_host(f_mode);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_ENGINE))
    {
        int f_val = atoi(a_value);
        assert(f_val == 0 || f_val == 1);
        pthread_spin_lock(&musikernel->main_lock);
        musikernel->is_offline_rendering = f_val;
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_PITCH_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_end = atof(f_arr->current_str);

        v_pydaw_pitch_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_CLEAN_WAV_POOL))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_LARGE_STRING);
        int f_uid;
        strcpy(f_arr->array, a_value);

        while(!f_arr->eof)
        {
            v_iterate_2d_char_array(f_arr);
            f_uid = atoi(f_arr->current_str);
            v_wav_pool_remove_item(musikernel->wav_pool, f_uid);
        }

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD))
    {
        int f_uid = atoi(a_value);
        t_wav_pool_item * f_old =
                g_wav_pool_get_item_by_uid(musikernel->wav_pool, f_uid);
        t_wav_pool_item * f_new =
                g_wav_pool_item_get(f_uid, f_old->path,
                musikernel->wav_pool->sample_rate);

        float * f_old_samples[2];
        f_old_samples[0] = f_old->samples[0];
        f_old_samples[1] = f_old->samples[1];

        pthread_spin_lock(&musikernel->main_lock);

        f_old->channels = f_new->channels;
        f_old->length = f_new->length;
        f_old->ratio_orig = f_new->ratio_orig;
        f_old->sample_rate = f_new->sample_rate;
        f_old->samples[0] = f_new->samples[0];
        f_old->samples[1] = f_new->samples[1];

        pthread_spin_unlock(&musikernel->main_lock);

        if(f_old_samples[0])
        {
            free(f_old_samples[0]);
        }

        if(f_old_samples[1])
        {
            free(f_old_samples[1]);
        }

        free(f_new);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }

}


/*Function for passing to plugins that re-use the wav pool*/
t_wav_pool_item * g_pydaw_wavpool_item_get(int a_uid)
{
    return g_wav_pool_get_item_by_uid(musikernel->wav_pool, a_uid);
}


/* Disable the optimizer for this function because it causes a
 * SEGFAULT on ARM (which could not be reproduced on x86)
 * This is not a performance-critical function. */
NO_OPTIMIZATION void v_pydaw_set_plugin_index(
        t_pytrack * f_track, int a_index, int a_plugin_index, int a_plugin_uid,
        int a_power, int a_lock)
{
    int f_i = 0;
    t_pydaw_plugin * f_plugin = NULL;

    if(a_plugin_index)
    {
        f_plugin = &musikernel->plugin_pool[a_plugin_uid];

        if(!f_plugin->active)
        {
            g_pydaw_plugin_init(
                f_plugin, (int)(musikernel->thread_storage[0].sample_rate),
                a_plugin_index, g_pydaw_wavpool_item_get,
                a_plugin_uid, v_queue_osc_message);

            char f_file_name[1024];
            snprintf(f_file_name, 1024, "%s%i",
                musikernel->plugins_folder, a_plugin_uid);

            if(i_pydaw_file_exists(f_file_name))
            {
                f_plugin->descriptor->load(f_plugin->PYFX_handle,
                    f_plugin->descriptor, f_file_name);
            }
        }
    }

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    if(f_plugin)
    {
        f_plugin->power = a_power;

        for(f_i = 0; f_i < f_track->channels; ++f_i)
        {
            f_plugin->descriptor->connect_buffer(
                f_plugin->PYFX_handle, f_i, f_track->buffers[f_i], 0);
            f_plugin->descriptor->connect_buffer(
                f_plugin->PYFX_handle, f_i, f_track->sc_buffers[f_i], 1);
        }
    }

    f_track->plugins[a_index] = f_plugin;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }
}

#endif	/* MUSIKERNEL_H */

