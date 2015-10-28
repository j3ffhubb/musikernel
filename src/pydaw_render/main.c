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

// Prevent importing LibLo
#define MK_DLL
// Prevent importing Portmidi
#define NO_MIDI

#define MK_OFFLINE_RENDER

#include <stdio.h>
#include <stdlib.h>
#include <sndfile.h>
#include <pthread.h>
#include <limits.h>

#include "../pydaw/src/compiler.h"
#include "../pydaw/src/mk_threads.h"
#include "../pydaw/include/pydaw_plugin.h"
#include "../pydaw/libmodsynth/lib/lmalloc.h"
#include <unistd.h>

int dawnext_main(int argc, char** argv);
void print_help();
int main(int argc, char** argv);

void print_help()
{
    printf("Usage:\n");
    printf("%s_render dawnext [project_dir] [output_file] [start_beat] "
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
    else if(!strcmp(argv[1], "dawnext"))
    {
        return dawnext_main(argc, argv);
    }
    else
    {
        print_help();
        return 1;
    }
}

int dawnext_main(int argc, char** argv)
{
    if(argc < 11)
    {
        print_help();
        return 1;
    }

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

    float** f_output;
    hpalloc((void**)&f_output, sizeof(float*) * 2);

    v_pydaw_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 0);

    /*
    PYDAW_AUDIO_INPUT_TRACK_COUNT = 2;
    v_pydaw_activate(f_thread_count, 0, f_project_dir, f_sample_rate, NULL, 1);
    v_wn_test();
    */

    f_i = 0;
    while(f_i < 2)
    {
        hpalloc((void**)&f_output[f_i], sizeof(float) * f_buffer_size);
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

    v_dn_offline_render_prep(dawnext);

    v_dn_offline_render(dawnext, f_start_beat,
        f_end_beat, f_output_file, f_create_file, f_stem_render);

    v_pydaw_destructor();

    return 0;
}

#ifdef __linux__

void v_interleave_benchmark(int f_buffer_size)
{
    register int f_i;

    struct timespec f_start, f_finish;

    printf("\nRunning benchmark of interleaved vs. non-interleaved buffers\n");

    float ** f_non_interleaved;

    clalloc((void**)&f_non_interleaved, sizeof(float*) * 2);
    clalloc((void**)&f_non_interleaved[0], sizeof(float) * f_buffer_size);
    clalloc((void**)&f_non_interleaved[1], sizeof(float) * f_buffer_size);

    for(f_i = 0; f_i < f_buffer_size; ++f_i)
    {
        f_non_interleaved[0][f_i] = 1.0f;
        f_non_interleaved[1][f_i] = 1.0f;
    }

    float * f_interleaved;
    clalloc((void**)&f_interleaved, sizeof(float) * f_buffer_size * 2);

    int ITERATIONS = 10000000;
    float f_mult = 0.99999999f;

    for(f_i = 0; f_i < f_buffer_size * 2; ++f_i)
    {
        f_interleaved[f_i] = 1.0f;
    }

    register int f_i2;

    clock_gettime(CLOCK_REALTIME, &f_start);

    for(f_i = 0; f_i < ITERATIONS; ++f_i)
    {
        for(f_i2 = 0; f_i2 < f_buffer_size * 2; ++f_i2)
        {
            f_interleaved[f_i2] *= f_mult;
        }
    }

    clock_gettime(CLOCK_REALTIME, &f_finish);

    v_pydaw_print_benchmark("Interleaved: ", f_start, f_finish);

    clock_gettime(CLOCK_REALTIME, &f_start);

    for(f_i = 0; f_i < ITERATIONS; ++f_i)
    {
        for(f_i2 = 0; f_i2 < f_buffer_size; ++f_i2)
        {
            f_non_interleaved[0][f_i2] *= f_mult;
            f_non_interleaved[1][f_i2] *= f_mult;
        }
    }

    clock_gettime(CLOCK_REALTIME, &f_finish);

    v_pydaw_print_benchmark("Non-interleaved: ", f_start, f_finish);
}

#endif
