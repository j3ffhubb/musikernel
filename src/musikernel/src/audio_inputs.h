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

#ifndef AUDIO_INPUTS_H
#define	AUDIO_INPUTS_H

#ifdef	__cplusplus
extern "C" {
#endif

#include <sndfile.h>
#include <pthread.h>
#include <stdio.h>
#include "files.h"

//1 megabyte interleaved buffer per audio input
#define AUDIO_INPUT_REC_BUFFER_SIZE (1024 * 1024)

typedef struct
{
    int rec;
    int monitor;
    int channels;
    int stereo_ch;
    int output_track;
    int output_mode;  //0=normal,1=sidechain,2=both
    MKFLT vol, vol_linear;
    SF_INFO sf_info;
    SNDFILE * sndfile;
    MKFLT rec_buffers[2][AUDIO_INPUT_REC_BUFFER_SIZE]
        __attribute__((aligned(16)));
    int buffer_iterator[2];
    int current_buffer;
    int flush_last_buffer_pending;
    int buffer_to_flush;
}t_pyaudio_input;

void g_pyaudio_input_init(t_pyaudio_input *, MKFLT);

void g_pyaudio_input_init(t_pyaudio_input * f_result, MKFLT a_sr)
{
    f_result->channels = 1;
    f_result->stereo_ch = -1;
    f_result->sf_info.channels = 1;
    f_result->sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_result->sf_info.samplerate = (int)(a_sr);

    f_result->sndfile = NULL;

    f_result->buffer_iterator[0] = 0;
    f_result->buffer_iterator[1] = 0;

    register int f_i;

    for(f_i = 0; f_i < AUDIO_INPUT_REC_BUFFER_SIZE; ++f_i)
    {
        f_result->rec_buffers[0][f_i] = 0.0f;
        f_result->rec_buffers[1][f_i] = 0.0f;
    }

    f_result->rec = 0;
    f_result->monitor = 0;
    f_result->current_buffer = 0;
    f_result->buffer_to_flush = 0;
    f_result->flush_last_buffer_pending = 0;
    f_result->output_track = 0;
    f_result->output_mode = 0;
    f_result->vol = 0.0f;
    f_result->vol_linear = 1.0f;
}

void v_audio_input_record_set(
        t_pyaudio_input * self, char * a_file_out)
{
    if(self->sndfile)
    {
        sf_close(self->sndfile);
        self->sndfile = NULL;
    }

    if(i_file_exists(a_file_out))
    {
        remove(a_file_out);
    }

    if(self->rec)
    {
        if(self->stereo_ch == -1)
        {
            self->channels = 1;
            self->sf_info.channels = 1;
        }
        else
        {
            self->channels = 2;
            self->sf_info.channels = 2;
        }

        self->sndfile = sf_open(a_file_out, SFM_WRITE, &self->sf_info);
    }
}


#ifdef	__cplusplus
}
#endif

#endif	/* AUDIO_INPUTS_H */

