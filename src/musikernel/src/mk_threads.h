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

#ifndef MK_THREADS_H
#define MK_THREADS_H

#ifdef SCHED_DEADLINE
    //#define RT_SCHED SCHED_DEADLINE
    #define RT_SCHED SCHED_FIFO
#else
    #define RT_SCHED SCHED_FIFO
#endif

#include "daw.h"
#include "wave_edit.h"

#ifdef MACOS
#include <sys/param.h>
#include <sys/sysctl.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

int READY = 0;

void * v_pydaw_worker_thread(void*);
void v_pydaw_init_worker_threads(int, int, int);
void v_open_project(const char*, int);

#ifdef __cplusplus
}
#endif

void v_pydaw_open_tracks()
{
    v_wn_open_tracks();
}

void v_open_project(const char* a_project_folder, int a_first_load)
{
#ifdef __linux__
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    sprintf(musikernel->project_folder, "%s", a_project_folder);
    sprintf(musikernel->plugins_folder, "%s%sprojects%splugins%s",
        musikernel->project_folder, PATH_SEP, PATH_SEP, PATH_SEP);
    sprintf(musikernel->samples_folder, "%s%saudio%ssamples",
        musikernel->project_folder, PATH_SEP, PATH_SEP);  //No trailing slash
    sprintf(musikernel->samplegraph_folder, "%s%saudio%ssamplegraph",
        musikernel->project_folder, PATH_SEP, PATH_SEP);  //No trailing slash

    sprintf(musikernel->wav_pool->samples_folder, "%s",
        musikernel->samples_folder);

    sprintf(musikernel->wav_pool_file, "%s%saudio%swavs.txt",
        musikernel->project_folder, PATH_SEP, PATH_SEP);
    sprintf(musikernel->audio_folder, "%s%saudio%sfiles",
        musikernel->project_folder, PATH_SEP, PATH_SEP);
    sprintf(musikernel->audio_tmp_folder, "%s%saudio%sfiles%stmp%s",
        musikernel->project_folder, PATH_SEP, PATH_SEP, PATH_SEP, PATH_SEP);

    if(a_first_load && i_pydaw_file_exists(musikernel->wav_pool_file))
    {
        v_wav_pool_add_items(musikernel->wav_pool, musikernel->wav_pool_file);
    }

    v_wn_open_project();
    v_dn_open_project(a_first_load);

#ifdef __linux__
    clock_gettime(CLOCK_REALTIME, &f_finish);
    v_pydaw_print_benchmark("v_open_project", f_start, f_finish);
#endif
}

void v_pydaw_activate(
    int a_thread_count,
    int a_set_thread_affinity,
    char* a_project_path,
    MKFLT a_sr,
    t_midi_device_list* a_midi_devices,
    int a_aux_threads
){
    /* Instantiate hosts */
    g_musikernel_get(a_sr, a_midi_devices);

    musikernel->hosts[MK_HOST_DAW].run = v_dn_run_engine;
    musikernel->hosts[MK_HOST_DAW].osc_send = v_dn_osc_send;
    musikernel->hosts[MK_HOST_DAW].audio_inputs = v_dn_update_audio_inputs;
    musikernel->hosts[MK_HOST_DAW].mix = v_default_mix;

    musikernel->hosts[MK_HOST_WAVENEXT].run = v_pydaw_run_wave_editor;
    musikernel->hosts[MK_HOST_WAVENEXT].osc_send = v_wn_osc_send;
    musikernel->hosts[MK_HOST_WAVENEXT].audio_inputs = v_wn_update_audio_inputs;
    musikernel->hosts[MK_HOST_WAVENEXT].mix = v_default_mix;

    g_dn_instantiate();
    g_wave_edit_get();

    v_open_project(a_project_path, 1);

    char * f_host_str = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
    get_file_setting(f_host_str, "host", "0");
    int f_host = atoi(f_host_str);
    printf("Last host:  %i\n", f_host);
    free(f_host_str);

    v_pydaw_set_host(f_host);

    v_pydaw_init_worker_threads(
        a_thread_count,
        a_set_thread_affinity,
        a_aux_threads
    );

#ifdef __linux__
    mlockall(MCL_CURRENT | MCL_FUTURE);
#endif

    READY = 1;
}

void v_pydaw_destructor()
{
    int f_i;

    char tmp_sndfile_name[2048];

    pthread_mutex_lock(&musikernel->audio_inputs_mutex);
    musikernel->audio_recording_quit_notifier = 1;
    pthread_mutex_unlock(&musikernel->audio_inputs_mutex);

    for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        if(musikernel->audio_inputs[f_i].sndfile)
        {
            sf_close(musikernel->audio_inputs[f_i].sndfile);
            sprintf(tmp_sndfile_name, "%s%i.wav",
                    musikernel->audio_tmp_folder, f_i);
            printf("Deleting %s\n", tmp_sndfile_name);
            remove(tmp_sndfile_name);
        }
    }

    pthread_spin_lock(&musikernel->main_lock);

    for(f_i = 1; f_i < musikernel->worker_thread_count; ++f_i)
    {
        pthread_mutex_lock(&musikernel->track_block_mutexes[f_i]);
        musikernel->track_thread_quit_notifier[f_i] = 1;
        pthread_cond_broadcast(&musikernel->track_cond[f_i]);
        pthread_mutex_unlock(&musikernel->track_block_mutexes[f_i]);
    }

    pthread_spin_unlock(&musikernel->main_lock);

    usleep(300000);

#ifdef WITH_LIBLO
    lo_address_free(musikernel->uiTarget);
#endif

    //abort the application rather than hang indefinitely
    for(f_i = 1; f_i < musikernel->worker_thread_count; ++f_i)
    {
        assert(musikernel->track_thread_quit_notifier[f_i] == 2);
    }
}


void * v_pydaw_osc_send_thread(void* a_arg)
{
    t_osc_send_data f_send_data;
    int f_i = 0;

    while(f_i < PYDAW_OSC_SEND_QUEUE_SIZE)
    {
        hpalloc((void**)&f_send_data.osc_queue_vals[f_i],
            sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
        ++f_i;
    }

    hpalloc((void**)&f_send_data.f_tmp1,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
    hpalloc((void**)&f_send_data.f_tmp2,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
    hpalloc((void**)&f_send_data.f_msg,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);

    f_send_data.f_tmp1[0] = '\0';
    f_send_data.f_tmp2[0] = '\0';
    f_send_data.f_msg[0] = '\0';

    while(!musikernel->audio_recording_quit_notifier)
    {
        musikernel->current_host->osc_send(&f_send_data);

        usleep(20000);
    }

    printf("osc send thread exiting\n");

    return (void*)1;
}

void v_pre_fault_thread_stack(int stacksize)
{
#ifdef __linux__
    int pagesize = sysconf(_SC_PAGESIZE);
    stacksize -= pagesize * 20;

    volatile char buffer[stacksize];
    int i;

    for (i = 0; i < stacksize; i += pagesize)
    {
        buffer[i] = i;
    }

    if(buffer[0]){}  //avoid a compiler warning
#endif
}

NO_OPTIMIZATION void v_self_set_thread_affinity()
{
    v_pre_fault_thread_stack(1024 * 512);

#ifdef __linux__
    pthread_attr_t threadAttr;
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(" Attempting to set pthread_self to .__sched_priority = %i\n",
            param.__sched_priority);
    pthread_attr_init(&threadAttr);
    pthread_attr_setschedparam(&threadAttr, &param);
    pthread_attr_setstacksize(&threadAttr, 1024 * 1024);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    pthread_t f_self = pthread_self();
    pthread_setschedparam(f_self, RT_SCHED, &param);
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    pthread_setaffinity_np(f_self, sizeof(cpu_set_t), &cpuset);

    pthread_attr_destroy(&threadAttr);
#endif
}

void * v_pydaw_worker_thread(void* a_arg)
{
    t_pydaw_thread_args * f_args = (t_pydaw_thread_args*)(a_arg);
    t_mk_thread_storage * f_storage =
        &musikernel->thread_storage[f_args->thread_num];
    v_pre_fault_thread_stack(f_args->stack_size);

    int f_thread_num = f_args->thread_num;
    pthread_cond_t * f_track_cond = &musikernel->track_cond[f_thread_num];
    pthread_mutex_t * f_track_block_mutex =
        &musikernel->track_block_mutexes[f_thread_num];
    pthread_spinlock_t * f_lock = &musikernel->thread_locks[f_thread_num];

    while(1)
    {
        pthread_cond_wait(f_track_cond, f_track_block_mutex);
        pthread_spin_lock(f_lock);

        if(musikernel->track_thread_quit_notifier[f_thread_num])
        {
            pthread_spin_unlock(f_lock);
            musikernel->track_thread_quit_notifier[f_thread_num] = 2;
            printf("Worker thread %i exiting...\n", f_thread_num);
            break;
        }

        if(f_storage->current_host == MK_HOST_DAW)
        {
            v_dn_process(f_args);
        }
        //else if...

        pthread_spin_unlock(f_lock);
    }

    return (void*)1;
}

int getNumberOfCores() {
#ifdef WIN32
    return atoi(getenv("NUMBER_OF_PROCESSORS"));
#elif MACOS
    int nm[2];
    size_t len = 4;
    uint32_t count;

    nm[0] = CTL_HW;
    nm[1] = HW_AVAILCPU;
    sysctl(nm, 2, &count, &len, NULL, 0);

    if(count < 1) {
        nm[1] = HW_NCPU;
        sysctl(nm, 2, &count, &len, NULL, 0);
        if(count < 1){
            count = 1;
        }
    }
    return count;
#elif __linux__
    return sysconf(_SC_NPROCESSORS_ONLN);
#else
    return 1;
#endif
}

void v_pydaw_init_worker_threads(
    int a_thread_count,
    int a_set_thread_affinity,
    int a_aux_threads
){
    int f_stack_size = (1024 * 1024);
    int f_cpu_core_inc = 1;
    int f_cpu_count = getNumberOfCores();
    printf("Detected %i cpu cores\n", f_cpu_count);

    if(f_cpu_count < 1)
    {
        f_cpu_count = 1;
    }

    if(a_thread_count == 0){  // auto, select for the user
        // 2 thread SMT is assumed now
        int core_count = f_cpu_count / 2;
        if(core_count >= 6){
            musikernel->worker_thread_count = 4;
        } else if(core_count >= 4){
            musikernel->worker_thread_count = 3;
        } else if(core_count == 3){
            musikernel->worker_thread_count = 2;
        } else {
            musikernel->worker_thread_count = 1;
        }
    } else {
        if(a_thread_count > f_cpu_count){
            musikernel->worker_thread_count = f_cpu_count;
        } else {
            musikernel->worker_thread_count = a_thread_count;
        }
    }

    if((musikernel->worker_thread_count * 2) <= f_cpu_count){
        f_cpu_core_inc = f_cpu_count / musikernel->worker_thread_count;

        if(f_cpu_core_inc < 2){
            f_cpu_core_inc = 2;
        } else if(f_cpu_core_inc > 4){
            f_cpu_core_inc = 4;
        }
    }

    printf("Spawning %i worker threads\n", musikernel->worker_thread_count);

    musikernel->track_block_mutexes = (pthread_mutex_t*)malloc(
        sizeof(pthread_mutex_t) * (musikernel->worker_thread_count));
    musikernel->worker_threads = (pthread_t*)malloc(
        sizeof(pthread_t) * (musikernel->worker_thread_count));

    hpalloc((void**)&musikernel->track_thread_quit_notifier,
        (sizeof(int) * (musikernel->worker_thread_count)));

    hpalloc((void**)&musikernel->track_cond,
        sizeof(pthread_cond_t) * (musikernel->worker_thread_count));

    hpalloc((void**)&musikernel->thread_locks,
        sizeof(pthread_spinlock_t) * (musikernel->worker_thread_count));

    pthread_attr_t threadAttr;
    pthread_attr_init(&threadAttr);

#ifdef __linux__
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(" Attempting to set .__sched_priority = %i\n",
            param.__sched_priority);
    pthread_attr_setschedparam(&threadAttr, &param);
#endif

    pthread_attr_setstacksize(&threadAttr, f_stack_size);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    //pthread_t f_self = pthread_self();
    //pthread_setschedparam(f_self, RT_SCHED, &param);

    int f_cpu_core = 0;
    int f_i;

    for(f_i = 0; f_i < (musikernel->worker_thread_count); ++f_i)
    {
        musikernel->track_thread_quit_notifier[f_i] = 0;
        t_pydaw_thread_args * f_args = (t_pydaw_thread_args*)malloc(
            sizeof(t_pydaw_thread_args)
        );
        f_args->thread_num = f_i;
        f_args->stack_size = f_stack_size;

        if(f_i == 0){
            musikernel->main_thread_args = (void*)f_args;
        }
        //pthread_mutex_init(&musikernel->track_cond_mutex[f_i], NULL);
        pthread_cond_init(&musikernel->track_cond[f_i], NULL);
        pthread_spin_init(&musikernel->thread_locks[f_i], 0);
        pthread_mutex_init(&musikernel->track_block_mutexes[f_i], NULL);
        pthread_create(
            &musikernel->worker_threads[f_i],
            &threadAttr,
            v_pydaw_worker_thread,
            (void*)f_args
        );

#ifdef __linux__
        if(a_set_thread_affinity){
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(f_cpu_core, &cpuset);
            pthread_setaffinity_np(
                    musikernel->worker_threads[f_i],
                    sizeof(cpu_set_t),
                    &cpuset
            );
            printf(
                    "Locked thread %i to core %i\n",
                    f_i,
                    f_cpu_core
            );
            //sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
            f_cpu_core += f_cpu_core_inc;
        }

        struct sched_param param2;
        int f_applied_policy = 0;
        pthread_getschedparam(musikernel->worker_threads[f_i],
            &f_applied_policy, &param2);

        if(f_applied_policy == RT_SCHED){
            printf("Scheduling successfully applied with priority %i\n ",
                    param2.__sched_priority);
        } else {
            printf("Scheduling was not successfully applied\n");
        }
#endif
    }

    pthread_attr_destroy(&threadAttr);
    musikernel->audio_recording_quit_notifier = 0;

    if(a_aux_threads){
        pthread_attr_t auxThreadAttr;
        pthread_attr_init(&auxThreadAttr);
        pthread_attr_setdetachstate(&auxThreadAttr, PTHREAD_CREATE_DETACHED);
        pthread_attr_setstacksize(&auxThreadAttr, (1024 * 1024));

        pthread_create(
            &musikernel->audio_recording_thread,
            &auxThreadAttr,
            v_pydaw_audio_recording_thread,
            NULL
        );

        pthread_create(
            &musikernel->osc_queue_thread,
            &auxThreadAttr,
            v_pydaw_osc_send_thread,
            (void*)musikernel
        );
        pthread_attr_destroy(&auxThreadAttr);
    }
}

#endif  /* MK_THREADS_H */
