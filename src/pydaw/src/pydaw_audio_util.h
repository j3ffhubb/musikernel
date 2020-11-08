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

#ifndef PYDAW_AUDIO_UTIL_H
#define	PYDAW_AUDIO_UTIL_H

#include <sndfile.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include "../libmodsynth/lib/interpolate-cubic.h"
#include "../libmodsynth/lib/pitch_core.h"
#include "pydaw_files.h"

#ifdef	__cplusplus
extern "C" {
#endif


#ifdef	__cplusplus
}
#endif


/*For time(affecting pitch) time stretching...  Since this is done
 offline anyways, it's not super optimized... */
void v_pydaw_rate_envelope(char * a_file_in, char * a_file_out,
        MKFLT a_start_rate, MKFLT a_end_rate)
{
    SF_INFO info;
    SNDFILE *file;
    MKFLT *tmpFrames;

    info.format = 0;
    file = sf_open(a_file_in, SFM_READ, &info);

    if (!file)
    {
        assert(0);
    }

    if (info.frames > 100000000)
    {
	//TODO:  Something, anything....
    }

    //!!! complain also if more than 2 channels

    tmpFrames = (MKFLT *)malloc(info.frames * info.channels * sizeof(MKFLT));
    mk_read_audio(file, tmpFrames, info.frames);

    SF_INFO f_sf_info;
    f_sf_info.channels = info.channels;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = info.samplerate;
    sf_close(file);

    MKFLT f_sample_pos = 0.0;

    long f_size = 0;
    long f_block_size = 5000;

    MKFLT * f_output = (MKFLT*)malloc(sizeof(MKFLT) * (f_block_size * 2));

    MKFLT * f_buffer0 = 0;
    MKFLT * f_buffer1 = 0;
    int f_i = 0;

    if(info.channels == 1)
    {
        f_buffer0 = tmpFrames;
    }
    else if(info.channels == 2)
    {
        f_buffer0 = (MKFLT*)malloc(sizeof(MKFLT) * info.frames);
        f_buffer1 = (MKFLT*)malloc(sizeof(MKFLT) * info.frames);

        int f_i2 = 0;
        //De-interleave...
        while(f_i < (info.frames * 2))
        {
            f_buffer0[f_i2] = tmpFrames[f_i];
            f_i++;
            f_buffer1[f_i2] = tmpFrames[f_i];
            f_i++;
            f_i2++;
        }
    }
    else
    {
        printf("\nMore than 2 channels not yet supported, "
                "you should remind me to do it\n");
        assert(0);
    }

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    while(((int)f_sample_pos) < info.frames)
    {
        f_size = 0;

        while(f_size < f_block_size)
        {
            if(info.channels == 1)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
            }
            else if(info.channels == 2)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer1, info.frames,
                        f_sample_pos);
                f_size++;
            }

            double f_rate = (((double)(a_end_rate - a_start_rate)) *
                (f_sample_pos / ((double)(info.frames)))) + a_start_rate;

            f_sample_pos += f_rate;

            if((int)f_sample_pos >= info.frames)
            {
                break;
            }
        }

        if(info.channels == 1)
        {
            mk_write_audio(f_sndfile, f_output, f_size);
        }
        else if(info.channels == 2)
        {
            mk_write_audio(f_sndfile, f_output, f_size / 2);
        }
    }

    sf_close(f_sndfile);

    char f_tmp_finished[2048];
    snprintf(f_tmp_finished, 2048, "%s.finished", a_file_out);
    FILE * f_finished = fopen(f_tmp_finished, "w");
    fclose(f_finished);
    free(f_output);
    free(f_buffer0);
    if(f_buffer1)
    {
        free(f_buffer1);
    }
    if(info.channels > 1)
    {
        free(tmpFrames);
    }
}



/*For pitch(affecting time) pitch shifting...  Since this is done
 offline anyways, it's not super optimized... */
void v_pydaw_pitch_envelope(char * a_file_in, char * a_file_out,
        MKFLT a_start_pitch, MKFLT a_end_pitch)
{
    SF_INFO info;
    SNDFILE *file;
    MKFLT *tmpFrames;

    info.format = 0;
    file = sf_open(a_file_in, SFM_READ, &info);

    if (!file)
    {
        assert(0);
    }

    if (info.frames > 100000000)
    {
	//TODO:  Something, anything....
    }

    //!!! complain also if more than 2 channels

    tmpFrames = (MKFLT *)malloc(info.frames * info.channels * sizeof(MKFLT));
    mk_read_audio(file, tmpFrames, info.frames);

    SF_INFO f_sf_info;
    f_sf_info.channels = info.channels;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = info.samplerate;
    sf_close(file);

    MKFLT f_sample_pos = 0.0;

    long f_size = 0;
    long f_block_size = 10000;

    MKFLT * f_output = (MKFLT*)malloc(sizeof(MKFLT) * (f_block_size * 2));

    MKFLT * f_buffer0 = 0;
    MKFLT * f_buffer1 = 0;
    int f_i = 0;

    t_pit_ratio * f_pit_ratio = g_pit_ratio();

    if(info.channels == 1)
    {
        f_buffer0 = tmpFrames;
    }
    else if(info.channels == 2)
    {
        f_buffer0 = (MKFLT*)malloc(sizeof(MKFLT) * info.frames);
        f_buffer1 = (MKFLT*)malloc(sizeof(MKFLT) * info.frames);

        int f_i2 = 0;
        //De-interleave...
        while(f_i < (info.frames * 2))
        {
            f_buffer0[f_i2] = tmpFrames[f_i];
            f_i++;
            f_buffer1[f_i2] = tmpFrames[f_i];
            f_i++;
            f_i2++;
        }
    }
    else
    {
        printf("\nMore than 2 channels not yet supported, "
                "you should remind me to do it\n");
        assert(0);
    }

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    while(((int)f_sample_pos) < info.frames)
    {
        f_size = 0;

        //Interleave the samples...
        while(f_size < f_block_size)
        {
            if(info.channels == 1)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
            }
            else if(info.channels == 2)
            {
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer0, info.frames,
                        f_sample_pos);
                f_size++;
                f_output[f_size] =
                    f_cubic_interpolate_ptr_wrap(f_buffer1, info.frames,
                        f_sample_pos);
                f_size++;
            }

            double f_rate = (((double)(a_end_pitch - a_start_pitch)) *
                (f_sample_pos / ((double)(info.frames)))) + a_start_pitch;

            MKFLT f_inc = f_pit_midi_note_to_ratio_fast(
                60.0f, f_rate + 60.0f, f_pit_ratio);

            f_sample_pos += f_inc;

            if((int)f_sample_pos >= info.frames)
            {
                break;
            }
        }

        if(info.channels == 1)
        {
            mk_write_audio(f_sndfile, f_output, f_size);
        }
        else if(info.channels == 2)
        {
            mk_write_audio(f_sndfile, f_output, f_size / 2);
        }
    }

    sf_close(f_sndfile);

    char f_tmp_finished[2048];
    snprintf(f_tmp_finished, 2048, "%s.finished", a_file_out);
    FILE * f_finished = fopen(f_tmp_finished, "w");
    fclose(f_finished);
    free(f_output);
    free(f_buffer0);
    if(f_buffer1)
    {
        free(f_buffer1);
    }
    if(info.channels > 1)
    {
        free(tmpFrames);
    }

    free(f_pit_ratio);
}


#endif	/* PYDAW_AUDIO_UTIL_H */

