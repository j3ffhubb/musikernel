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


//Required for sched.h
#ifndef __USE_GNU
#define __USE_GNU
#endif

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <sndfile.h>
#include <pthread.h>
#include <limits.h>
#include <portaudio.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <signal.h>
#include <dirent.h>
#include <time.h>
#include <errno.h>

#ifdef __linux__
#include <linux/sched.h>
#include <sys/resource.h>
#endif

#include "compiler.h"
#include "files.h"
#include "plugin.h"
#include "libmodsynth/lib/lmalloc.h"
#include "mk_threads.h"

#ifndef NO_MIDI
    #include "midi_device.h"
    t_midi_device_list MIDI_DEVICES;
    PmError f_midi_err;
#endif

#define CLOCKID CLOCK_REALTIME
#define SIG SIGRTMIN

#define PA_SAMPLE_TYPE paFloat32
#define DEFAULT_FRAMES_PER_BUFFER 512

void _mk_exit()
{
#ifndef NO_MIDI
    Pm_Terminate();
#endif
    PaError err = Pa_Terminate();
    if(err != paNoError)
    {
        printf("Pa_Terminate error:  %s\n", Pa_GetErrorText(err));
    }
}

#ifdef MK_DLL
    #define mk_exit(x) _mk_exit(); return x
#else
    #define mk_exit(x) _mk_exit(); exit(x)
#endif

#define RET_CODE_DEVICE_NOT_FOUND 1000
#define RET_CODE_CONFIG_NOT_FOUND 1001
#define RET_CODE_AUDIO_DEVICE_ERROR 1002
#define RET_CODE_AUDIO_DEVICE_BUSY 1003


#if defined(__linux__) && !defined(MK_DLL)
static sigset_t _signals;
#endif

int NO_HARDWARE = 0;

#ifdef WITH_LIBLO
lo_server_thread serverThread;

void osc_error(int num, const char *m, const char *path);

int osc_message_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;
int osc_debug_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;
#endif

/* Does this still serve a purpose?  TODO:  try deleting it */
#if defined(_WIN32)
int main(int argc, char **argv);
int v_configure(const char * path, const char * key, const char * value);
#endif

int daw_main(int argc, char** argv);
void print_help();
int main(int argc, char** argv);
int main_loop(int argc, char **argv);
inline void v_run_main_loop(
    int sample_count,
    MKFLT **output,
    MKFLT *a_input_buffers
);

void signalHandler(int sig)
{
    printf("signal %d caught, trying to clean up and exit\n", sig);
    pthread_mutex_lock(&musikernel->exit_mutex);
    exiting = 1;
    pthread_mutex_unlock(&musikernel->exit_mutex);
}


inline void v_run(MKFLT ** buffers, MKFLT * a_input, int sample_count)
{
    pthread_spin_lock(&musikernel->main_lock);

    if(likely(!musikernel->is_offline_rendering)){
        v_run_main_loop(sample_count, buffers, a_input);
    } else {
        /*Clear the output buffer*/
        int f_i;

        for(f_i = 0; f_i < sample_count; ++f_i){
            buffers[0][f_i] = 0.0f;
            buffers[1][f_i] = 0.0f;
        }
    }

    pthread_spin_unlock(&musikernel->main_lock);
}

inline void v_run_main_loop(int sample_count,
        MKFLT ** a_buffers, PYFX_Data *a_input_buffers)
{
    musikernel->current_host->run(sample_count, a_buffers, a_input_buffers);

    if(unlikely(musikernel->is_previewing))
    {
        register int f_i;
        t_audio_item * f_audio_item = musikernel->preview_audio_item;
        t_wav_pool_item * f_wav_item = musikernel->preview_wav_item;
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            if(f_audio_item->sample_read_heads[0].whole_number >=
                f_wav_item->length)
            {
                musikernel->is_previewing = 0;
                break;
            }
            else
            {
                v_adsr_run(&f_audio_item->adsrs[0]);
                if(f_wav_item->channels == 1)
                {
                    MKFLT f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)) *
                        (f_audio_item->adsrs[0].output) *
                        (musikernel->preview_amp_lin); // *
                        //(f_audio_item->fade_vol);

                    a_buffers[0][f_i] = f_tmp_sample;
                    a_buffers[1][f_i] = f_tmp_sample;
                }
                else if(f_wav_item->channels > 1)
                {
                    a_buffers[0][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)
                    ) * f_audio_item->adsrs[0].output *
                        musikernel->preview_amp_lin; // *
                        //(f_audio_item->fade_vol);

                    a_buffers[1][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[1]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)
                    ) * f_audio_item->adsrs[0].output *
                        musikernel->preview_amp_lin; // *
                        //(f_audio_item->fade_vol);
                }

                v_ifh_run(&f_audio_item->sample_read_heads[0],
                        f_audio_item->ratio);

                if((f_audio_item->sample_read_heads[0].whole_number)
                    >= (musikernel->preview_max_sample_count))
                {
                    v_adsr_release(&f_audio_item->adsrs[0]);
                }

                if(f_audio_item->adsrs[0].stage == ADSR_STAGE_OFF)
                {
                    musikernel->is_previewing = 0;
                    break;
                }
            }
        }
    }

    if(!musikernel->is_offline_rendering && MASTER_VOL != 1.0f)
    {
        register int f_i;
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            a_buffers[0][f_i] *= MASTER_VOL;
            a_buffers[1][f_i] *= MASTER_VOL;
        }
    }

    musikernel->current_host->mix();
}

int THREAD_AFFINITY = 0;
int THREAD_AFFINITY_SET = 0;

static int portaudioCallback(
    const void *inputBuffer,
    void *outputBuffer,
    unsigned long framesPerBuffer,
    const PaStreamCallbackTimeInfo* timeInfo,
    PaStreamCallbackFlags statusFlags,
    void *userData
){
    musikernel->out = (float*)outputBuffer;
    MKFLT *in = (MKFLT*)inputBuffer;

    if(unlikely(framesPerBuffer > FRAMES_PER_BUFFER))
    {
        printf("WARNING:  Audio device requested buffer size %i, "
            "truncating to max buffer size:  %i\n",
            (int)framesPerBuffer, FRAMES_PER_BUFFER);
        framesPerBuffer = FRAMES_PER_BUFFER;
    }

    // Try one time to set thread affinity
    if(unlikely(THREAD_AFFINITY && !THREAD_AFFINITY_SET))
    {
        v_self_set_thread_affinity();
        THREAD_AFFINITY_SET = 1;
    }

    v_run(pluginOutputBuffers, in, framesPerBuffer);

    return paContinue;
}

typedef struct
{
    int pid;
}ui_thread_args;

NO_OPTIMIZATION void * ui_process_monitor_thread(
    void * a_thread_args)
{
    char f_proc_path[256];
    f_proc_path[0] = '\0';
    ui_thread_args * f_thread_args = (ui_thread_args*)(a_thread_args);
    sprintf(f_proc_path, "/proc/%i", f_thread_args->pid);
    struct stat sts;
    int f_exited = 0;

    while(!exiting)
    {
        sleep(1);
        if (stat(f_proc_path, &sts) == -1 && errno == ENOENT)
        {
            printf("UI process doesn't exist, exiting.\n");
            pthread_mutex_lock(&musikernel->exit_mutex);
            exiting = 1;
            pthread_mutex_unlock(&musikernel->exit_mutex);
            f_exited = 1;
            break;
        }
    }

    if(f_exited)
    {
        sleep(3);
        Pa_Terminate();
#ifndef NO_MIDI
        Pm_Terminate();
#endif
        exit(0);
    }

    return (void*)0;
}


void print_help()
{
    printf("Usage:\n");
    printf("%s install_prefix project_path ui_pid "
            "huge_pages[--sleep]\n\n", MUSIKERNEL_VERSION);
    printf("%s daw [project_dir] [output_file] [start_beat] "
        "[end_beat] [sample_rate] [buffer_size] [thread_count] "
        "[huge_pages] [stem]\n\n", MUSIKERNEL_VERSION);
}

int main(int argc, char** argv)
{
    if(argc < 2)
    {
        print_help();
        return 1;
    }
    else if(!strcmp(argv[1], "daw"))
    {
        return daw_main(argc, argv);
    }

    return main_loop(argc, argv);
}

int daw_main(int argc, char** argv)
{
    if(argc < 11)
    {
        print_help();
        return 1;
    }

    MK_OFFLINE_RENDER = 1;

    char * f_project_dir = argv[2];
    char * f_output_file = argv[3];
    double f_start_beat = atof(argv[4]);
    double f_end_beat = atof(argv[5]);
    int f_sample_rate = atoi(argv[6]);
    int f_buffer_size = atoi(argv[7]);
    int f_thread_count = atoi(argv[8]);

    int f_huge_pages = atoi(argv[9]);
    assert(f_huge_pages == 0 || f_huge_pages == 1);

    if(f_huge_pages)
    {
        printf("Attempting to use hugepages\n");
    }

    int f_stem_render = atoi(argv[10]);

    USE_HUGEPAGES = f_huge_pages;

    int f_create_file = 1;

    int f_i;
    for(f_i = 10; f_i < argc; ++f_i)
    {
        if(!strcmp(argv[f_i], "--no-file"))
        {
            f_create_file = 0;
        }
    }

    MKFLT** f_output;
    hpalloc((void**)&f_output, sizeof(MKFLT*) * 2);

    v_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 0);

    /*
    AUDIO_INPUT_TRACK_COUNT = 2;
    v_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 1);
    v_wn_test();
    */

    f_i = 0;
    while(f_i < 2)
    {
        hpalloc((void**)&f_output[f_i], sizeof(MKFLT) * f_buffer_size);
        f_i++;
    }

    f_i = 0;
    while(f_i < f_buffer_size)
    {
        f_output[0][f_i] = 0.0f;
        f_output[1][f_i] = 0.0f;
        f_i++;
    }

    musikernel->sample_count = f_buffer_size;

    v_dn_offline_render_prep(daw);

    v_dn_offline_render(daw, f_start_beat,
        f_end_beat, f_output_file, f_create_file, f_stem_render);

    v_destructor();

    return 0;
}

NO_OPTIMIZATION int main_loop(int argc, char **argv)
{
    if(argc < 5)
    {
        print_help();
        mk_exit(9996);
    }

    MKFLT sample_rate = 44100.0f;
    int f_thread_count = 0;
    int f_thread_affinity = 0;
    int f_performance = 0;
    int j;

    pthread_attr_t f_ui_threadAttr;
    pthread_attr_init(&f_ui_threadAttr);

#ifdef __linux__
    struct sched_param param;
    param.__sched_priority = 1; //90;
    pthread_attr_setschedparam(&f_ui_threadAttr, &param);
#endif

    pthread_attr_setstacksize(&f_ui_threadAttr, 1000000); //8388608);
    pthread_attr_setdetachstate(&f_ui_threadAttr, PTHREAD_CREATE_DETACHED);

#ifndef MK_DLL
    pthread_t f_ui_monitor_thread;
    ui_thread_args * f_ui_thread_args =
            (ui_thread_args*)malloc(sizeof(ui_thread_args));
    f_ui_thread_args->pid = atoi(argv[3]);
    pthread_create(&f_ui_monitor_thread, &f_ui_threadAttr,
            ui_process_monitor_thread, (void*)f_ui_thread_args);
#endif

    int f_huge_pages = atoi(argv[4]);
    assert(f_huge_pages == 0 || f_huge_pages == 1);

    if(f_huge_pages)
    {
        printf("Attempting to use hugepages\n");
    }

    USE_HUGEPAGES = f_huge_pages;

    j = 0;

    while(j < argc)
    {
        printf("%s\n", argv[j]);
        ++j;
    }

    int f_usleep = 0;

    if(argc > 5)
    {
        j = 5;
        while(j < argc)
        {
            if(!strcmp(argv[j], "--sleep"))
            {
                f_usleep = 1;
            }
            else
            {
                printf("Invalid argument [%i] %s\n", j, argv[j]);
            }
            ++j;
        }
    }

#if defined(__linux__) && !defined(MK_DLL)
    if(setpriority(PRIO_PROCESS, 0, -20))
    {
        printf("Unable to renice process (this was to be expected if "
            "the process is not running as root)\n");
    }

    int f_current_proc_sched = sched_getscheduler(0);

    if(f_current_proc_sched == RT_SCHED)
    {
        printf("Process scheduler already set to real-time.");
    }
    else
    {
        printf("\n\nProcess scheduler set to %i, attempting to set "
                "real-time scheduler.\n", f_current_proc_sched);
        //Attempt to set the process priority to real-time
        const struct sched_param f_proc_param =
                {sched_get_priority_max(RT_SCHED)};
        printf("Attempting to set scheduler for process\n");
        sched_setscheduler(0, RT_SCHED, &f_proc_param);
        printf("Process scheduler is now %i\n\n", sched_getscheduler(0));
    }

    setsid();
    sigemptyset (&_signals);
    sigaddset(&_signals, SIGHUP);
    sigaddset(&_signals, SIGINT);
    sigaddset(&_signals, SIGQUIT);
    sigaddset(&_signals, SIGPIPE);
    sigaddset(&_signals, SIGTERM);
    sigaddset(&_signals, SIGUSR1);
    sigaddset(&_signals, SIGUSR2);
    pthread_sigmask(SIG_BLOCK, &_signals, 0);

    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGHUP, signalHandler);
    signal(SIGQUIT, signalHandler);
    pthread_sigmask(SIG_UNBLOCK, &_signals, 0);
#endif

    j = 0;

    hpalloc(
        (void**)&pluginOutputBuffers,
        2 * sizeof(MKFLT*)
    );

    int f_i;
    for(f_i = 0; f_i < 2; ++f_i){
        hpalloc(
            (void**)&pluginOutputBuffers[f_i],
            sizeof(MKFLT) * FRAMES_PER_BUFFER
        );
    }

    /*Initialize Portaudio*/
    PaStreamParameters inputParameters, outputParameters;
    PaStream *stream;
    PaError err;
    err = Pa_Initialize();
    if(err != paNoError)
    {
        printf("Pa_Initialize error:  %s\n", Pa_GetErrorText(err));
    }
    /* default input device */

#ifndef NO_MIDI
    /*Initialize Portmidi*/
    f_midi_err = Pm_Initialize();
    MIDI_DEVICES.count = 0;
#endif

    char f_midi_device_name[1024];
    sprintf(f_midi_device_name, "None");

    char f_device_file_path[2048];

    char * f_home = get_home_dir();

    printf("using home folder: %s\n", f_home);

    char * path_list[4] = {
        f_home, MUSIKERNEL_VERSION, "config", "device.txt"
    };

    path_join(f_device_file_path, 4, path_list);

    char f_device_name[256];
    f_device_name[0] = '\0';

#if defined(_WIN32) || defined(__APPLE__)
    char f_input_name[256];
    f_input_name[0] = '\0';
#endif

    int f_frame_count = DEFAULT_FRAMES_PER_BUFFER;
    int f_audio_input_count = 0;
    int f_audio_output_count = 2;

#ifdef WITH_LIBLO

    /* Create OSC thread */

    serverThread = lo_server_thread_new("19271", osc_error);
    lo_server_thread_add_method(serverThread, NULL, NULL, osc_message_handler,
            NULL);
    lo_server_thread_start(serverThread);

#endif

    char * f_key_char = (char*)malloc(sizeof(char) * TINY_STRING);
    char * f_value_char = (char*)malloc(sizeof(char) * TINY_STRING);

    int f_api_count = Pa_GetHostApiCount();
    int f_host_api_index = -1;

    char f_host_apis[f_api_count][256];

    for(f_i = 0; f_i < f_api_count; ++f_i){
        snprintf(f_host_apis[f_i], 256, "%s", Pa_GetHostApiInfo(f_i)->name);
    }

    while(1){
        if(i_file_exists(f_device_file_path)){
            printf("device.txt exists\n");
            t_2d_char_array * f_current_string = g_get_2d_array_from_file(
                    f_device_file_path, LARGE_STRING);
            f_device_name[0] = '\0';
            f_host_api_index = -1;
#if defined(_WIN32) || defined(__APPLE__)
            f_input_name[0] = '\0';
#endif
            while(1)
            {
                v_iterate_2d_char_array(f_current_string);
                if(f_current_string->eof){
                    break;
                }
                if(
                    !strcmp(f_current_string->current_str, "") ||
                    f_current_string->eol
                ){
                    continue;
                }

                strcpy(f_key_char, f_current_string->current_str);
                v_iterate_2d_char_array_to_next_line(f_current_string);
                strcpy(f_value_char, f_current_string->current_str);

                if(!strcmp(f_key_char, "hostApi")){
                    for(f_i = 0; f_i < f_api_count; ++f_i)
                    {
                        if(!strcmp(f_value_char, f_host_apis[f_i]))
                        {
                            f_host_api_index = f_i;
                            break;
                        }
                    }
                    printf("host api: %s\n", f_value_char);
                    printf("host api index %i\n", f_host_api_index);
                } else if(!strcmp(f_key_char, "name")){
                    snprintf(f_device_name, 256, "%s", f_value_char);
                    printf("device name: \"%s\"\n", f_device_name);
                }
#if defined(_WIN32) || defined(__APPLE__)
                else if(!strcmp(f_key_char, "inputName")){
                    snprintf(f_input_name, 256, "%s", f_value_char);
                    printf("input name: %s\n", f_device_name);
                }
#endif
                else if(!strcmp(f_key_char, "bufferSize")){
                    f_frame_count = atoi(f_value_char);
                    printf("bufferSize: %i\n", f_frame_count);
                } else if(!strcmp(f_key_char, "audioEngine")){
                    int f_engine = atoi(f_value_char);
                    printf("audioEngine: %i\n", f_engine);
                    if(f_engine == 4 || f_engine == 5 || f_engine == 7){
                        NO_HARDWARE = 1;
                    } else {
                        NO_HARDWARE = 0;
                    }
                } else if(!strcmp(f_key_char, "sampleRate")){
                    sample_rate = atof(f_value_char);
                    printf("sampleRate: %i\n", (int)sample_rate);
                } else if(!strcmp(f_key_char, "threads")){
                    f_thread_count = atoi(f_value_char);
                    if(f_thread_count > 8){
                        f_thread_count = 8;
                    } else if(f_thread_count < 0){
                        f_thread_count = 0;
                    }
                    printf("threads: %i\n", f_thread_count);
                } else if(!strcmp(f_key_char, "threadAffinity")){
                    f_thread_affinity = atoi(f_value_char);
                    THREAD_AFFINITY = f_thread_affinity;
                    printf("threadAffinity: %i\n", f_thread_affinity);
                } else if(!strcmp(f_key_char, "performance")){
                    f_performance = atoi(f_value_char);

                    printf("performance: %i\n", f_performance);
                } else if(!strcmp(f_key_char, "midiInDevice")){
#ifndef NO_MIDI
                    sprintf(f_midi_device_name, "%s", f_value_char);
                    printf("midiInDevice: %s\n", f_value_char);
                    int f_device_result = midiDeviceInit(
                        &MIDI_DEVICES.devices[MIDI_DEVICES.count],
                        f_midi_device_name);

                    if(f_device_result == 0)
                    {
                        printf("Succeeded\n");
                    }
                    else if(f_device_result == 1)
                    {
                        printf("Error, did not find MIDI device\n");
                        /*++f_failure_count;
                        sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                            "Error: did not find MIDI device:",
                            f_midi_device_name);
                        system(f_cmd_buffer);
                        continue;*/
                    }
                    else if(f_device_result == 2)
                    {
                        printf("Error, opening MIDI device\n");
                        /*++f_failure_count;
                        sprintf(f_cmd_buffer, "%s \"%s %s, %s\"",
                            f_show_dialog_cmd, "Error opening MIDI device: ",
                            f_midi_device_name, Pm_GetErrorText(f_midi_err));
                        system(f_cmd_buffer);
                        continue;*/
                    }

                    ++MIDI_DEVICES.count;
#endif
                }
                else if(!strcmp(f_key_char, "audioInputs"))
                {
                    f_audio_input_count = atoi(f_value_char);
                    printf("audioInputs: %s\n", f_value_char);
                    assert(f_audio_input_count >= 0 &&
                        f_audio_input_count <= 128);
                    AUDIO_INPUT_TRACK_COUNT = f_audio_input_count;
                }
                else if(!strcmp(f_key_char, "audioOutputs"))
                {
                    t_line_split * f_line = g_split_line(
                        '|', f_value_char);
                    if(f_line->count != 3)
                    {
                        printf("audioOutputs: invalid value: '%s'\n",
                            f_value_char);
                        mk_exit(RET_CODE_CONFIG_NOT_FOUND);
                    }
                    printf("audioOutputs: %s\n", f_value_char);

                    f_audio_output_count = atoi(f_line->str_arr[0]);
                    assert(f_audio_output_count >= 1 &&
                        f_audio_output_count <= 128);
                    OUTPUT_CH_COUNT = f_audio_output_count;

                    MASTER_OUT_L = atoi(f_line->str_arr[1]);
                    assert(MASTER_OUT_L >= 0 &&
                        MASTER_OUT_L < f_audio_output_count);
                    MASTER_OUT_R = atoi(f_line->str_arr[2]);
                    assert(MASTER_OUT_R >= 0 &&
                        MASTER_OUT_R < f_audio_output_count);

                    v_free_split_line(f_line);
                }
                else
                {
                    printf("Unknown key|value pair: %s|%s\n",
                        f_key_char, f_value_char);
                }
            }

            g_free_2d_char_array(f_current_string);

        } else {
            printf("Device config not found\n");
            mk_exit(RET_CODE_CONFIG_NOT_FOUND);

        }

        inputParameters.channelCount = f_audio_input_count;
        inputParameters.sampleFormat = PA_SAMPLE_TYPE;
        inputParameters.hostApiSpecificStreamInfo = NULL;

        outputParameters.channelCount = f_audio_output_count;
        outputParameters.sampleFormat = PA_SAMPLE_TYPE;
        outputParameters.hostApiSpecificStreamInfo = NULL;

        int f_found_index = 0;
        for(f_i = 0; f_i < Pa_GetDeviceCount(); ++f_i){
            const PaDeviceInfo * f_padevice = Pa_GetDeviceInfo(f_i);
            printf("\"%s\" %i %i\n", f_padevice->name, f_padevice->hostApi,
                f_padevice->maxOutputChannels);
            if(
                !strcmp(f_padevice->name, f_device_name) &&
                f_host_api_index == f_padevice->hostApi
            ){
                if(!f_padevice->maxOutputChannels){
                    printf("Error:  PaDevice->maxOutputChannels == 0, "
                        "device may already be open by another application\n");
                    mk_exit(RET_CODE_AUDIO_DEVICE_BUSY);
                }

                outputParameters.device = f_i;
                inputParameters.device = f_i;
                f_found_index = 1;
                break;
            }
        }

        if(!f_found_index){
            printf("Device not found\n");
            mk_exit(RET_CODE_DEVICE_NOT_FOUND);
        }

        const PaDeviceInfo * f_device_info =
            Pa_GetDeviceInfo(outputParameters.device);

        outputParameters.suggestedLatency =
            f_device_info->defaultLowOutputLatency;

#if defined(_WIN32) || defined(__APPLE__)
        if(f_input_name[0] == '\0')
        {
            inputParameters.channelCount = 0;
        }
        else
        {
            f_found_index = 0;
            for(f_i = 0; f_i < Pa_GetDeviceCount(); ++f_i)
            {
                const PaDeviceInfo * f_padevice = Pa_GetDeviceInfo(f_i);
                if(
                    !strcmp(f_padevice->name, f_input_name) &&
                    f_host_api_index == f_padevice->hostApi &&
                    f_padevice->maxInputChannels
                ){
                    inputParameters.device = f_i;
                    f_found_index = 1;
                    break;
                }
            }

            if(!f_found_index)
            {
                printf("Device not found\n");
                mk_exit(RET_CODE_DEVICE_NOT_FOUND);
            }

            f_device_info = Pa_GetDeviceInfo(inputParameters.device);

            inputParameters.suggestedLatency =
                f_device_info->defaultLowInputLatency;
        }
#else
        inputParameters.device = outputParameters.device;
#endif

        if(!NO_HARDWARE)
        {
            PaStreamParameters * f_input_params = NULL;

            if(inputParameters.channelCount > 0)
            {
                f_input_params = &inputParameters;
            }

            err = Pa_OpenStream(
                &stream,
                f_input_params,
                &outputParameters,
                sample_rate,
                f_frame_count,
                0, // paClipOff
                portaudioCallback,
                NULL
            );

            if(err != paNoError)
            {
                printf("Error while opening audio device: %s",
                    Pa_GetErrorText(err));
                mk_exit(RET_CODE_AUDIO_DEVICE_ERROR);
            }
        }
        break;
    }

    char * f_master_vol_str = (char*)malloc(sizeof(char) * TINY_STRING);
    get_file_setting(f_master_vol_str, "master_vol", "0.0");
    MKFLT f_master_vol = atof(f_master_vol_str);
    free(f_master_vol_str);

    MASTER_VOL = f_db_to_linear(f_master_vol * 0.1);
    printf("MASTER_VOL = %f\n", MASTER_VOL);

    free(f_key_char);
    free(f_value_char);

#ifdef NO_MIDI
    v_activate(f_thread_count, f_thread_affinity, argv[2],
        sample_rate, NULL, 1);
#else
    v_activate(f_thread_count, f_thread_affinity, argv[2],
        sample_rate, &MIDI_DEVICES, 1);
#endif

    v_queue_osc_message("ready", "");

    // only for no-hardware mode
    MKFLT * f_portaudio_input_buffer = NULL;
    MKFLT * f_portaudio_output_buffer = NULL;

    if(!NO_HARDWARE)
    {
        err = Pa_StartStream(stream);
        if(err != paNoError)
        {
            printf("Error: Unknown error while starting device.  Please "
                "re-configure your device and try starting MusiKernel again.");
            mk_exit(RET_CODE_AUDIO_DEVICE_ERROR);
        }
        const PaStreamInfo * f_stream_info = Pa_GetStreamInfo(stream);
        printf("Actual output latency:\n\tmilliseconds:  %f\n\tsamples:  %i\n",
            (MKFLT)f_stream_info->outputLatency * 1000.0f,
            (int)(f_stream_info->outputLatency * f_stream_info->sampleRate));
        if((int)f_stream_info->sampleRate != (int)sample_rate)
        {
            printf("Warning:  Samplerate reported by the device does not "
                "match the selected sample rate.\n");
        }
    }
    else
    {
        lmalloc((void**)&f_portaudio_input_buffer,
            sizeof(MKFLT) * FRAMES_PER_BUFFER);
        lmalloc((void**)&f_portaudio_output_buffer,
            sizeof(MKFLT) * FRAMES_PER_BUFFER);

        for(f_i = 0; f_i < FRAMES_PER_BUFFER; ++f_i)
        {
            f_portaudio_input_buffer[f_i] = 0.0f;
            f_portaudio_output_buffer[f_i] = 0.0f;
        }
    }

    while(1)
    {
        pthread_mutex_lock(&musikernel->exit_mutex);
        if(exiting)
        {
            pthread_mutex_unlock(&musikernel->exit_mutex);
            break;
        }
        pthread_mutex_unlock(&musikernel->exit_mutex);


        if(NO_HARDWARE)
        {
            portaudioCallback(
                f_portaudio_input_buffer,
                f_portaudio_output_buffer, 128, NULL,
                (PaStreamCallbackFlags)NULL, NULL);

            if(f_usleep)
            {
                usleep(1000);
            }
        }
        else
        {
            sleep(1);
        }

    }

    if(!NO_HARDWARE)
    {
        err = Pa_CloseStream(stream);
        if(err != paNoError)
        {
            printf("Pa_CloseStream error:  %s\n", Pa_GetErrorText(err));

            usleep(50000);

            err = Pa_IsStreamStopped(stream);

            if(err < 1)
            {
                if(err == 0)
                    printf("Pa_IsStreamStopped returned 0 (WTF?)\n");
                if(err < 0)
                    printf("Pa_IsStreamStopped error:  %s\n",
                        Pa_GetErrorText(err));
                err = Pa_AbortStream(stream);
                if(err != paNoError)
                    printf("Pa_AbortStream error:  %s\n",
                        Pa_GetErrorText(err));
            }
        }
    }

#ifndef NO_MIDI
    for(f_i = 0; f_i < MIDI_DEVICES.count; ++f_i)
    {
        if(MIDI_DEVICES.devices[f_i].loaded)
        {
            midiDeviceClose(&MIDI_DEVICES.devices[f_i]);
        }
    }
#endif

    v_destructor();

#if defined(__linux__) && !defined(MK_DLL)

    sigemptyset(&_signals);
    sigaddset(&_signals, SIGHUP);
    pthread_sigmask(SIG_BLOCK, &_signals, 0);
    kill(0, SIGHUP);

#endif

    printf("MusiKernel main() returning\n\n\n");
    mk_exit(0);
}

int v_configure(const char * path, const char * key, const char * value)
{
    if(!READY)
    {
        int i;

        for(i = 0; i < 20; ++i)
        {
            usleep(100000);

            if(READY)
            {
                break;
            }
        }

        if(!READY)
        {
            return 1;
        }
    }

    if(!strcmp(path, "/musikernel/wave_edit"))
    {
        v_wn_configure(key, value);
        return 0;
    }
    else if(!strcmp(path, "/musikernel/daw"))
    {
        v_dn_configure(key, value);
        return 0;
    }
    else if(!strcmp(path, "/musikernel/master"))
    {
        v_mk_configure(key, value);
        return 0;
    }

    return 1;
}

#ifdef WITH_LIBLO

int osc_debug_handler(const char *path, const char *types, lo_arg **argv,
                      int argc, void *data, void *user_data)
{
    int f_i = 0;

    printf("got unhandled OSC message:\npath: <%s>\n", path);
    while(f_i < argc)
    {
        printf("arg %d '%c' ", f_i, types[f_i]);
        lo_arg_pp((lo_type)types[f_i], argv[f_i]);
        printf("\n");
        ++f_i;
    }

    return 1;
}

int osc_message_handler(const char *path, const char *types, lo_arg **argv,
                        int argc, void *data, void *user_data)
{
    const char *key = (const char *)&argv[0]->s;
    const char *value = (const char *)&argv[1]->s;

    assert(!strcmp(types, "ss"));


    if(v_configure(path, key, value))
    {
        return osc_debug_handler(path, types, argv, argc, data, user_data);
    }
    else
    {
        return 0;
    }
}

#endif

