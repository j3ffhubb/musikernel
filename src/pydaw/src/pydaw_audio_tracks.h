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

#ifndef PYDAW_AUDIO_TRACKS_H
#define	PYDAW_AUDIO_TRACKS_H

#include <sndfile.h>
#include "../libmodsynth/lib/amp.h"
#include "../libmodsynth/lib/pitch_core.h"
#include "../libmodsynth/lib/interpolate-cubic.h"
//Imported only for t_int_frac_read_head... TODO:  Fork that into it's own file...
#include "../libmodsynth/lib/interpolate-sinc.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "../libmodsynth/modules/modulation/adsr.h"
#include "../libmodsynth/modules/filter/svf.h"
#include "../include/pydaw_plugin.h"
#include "pydaw_files.h"


#define PYDAW_MAX_AUDIO_ITEM_COUNT 256
#define PYDAW_MAX_WAV_POOL_ITEM_COUNT 500

#define PYDAW_AUDIO_ITEM_PADDING 64
#define PYDAW_AUDIO_ITEM_PADDING_DIV2 32
#define PYDAW_AUDIO_ITEM_PADDING_DIV2_FLOAT 32.0f

#define MK_AUDIO_ITEM_SEND_COUNT 3

#define MK_PAIF_PER_ITEM 8

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT a_knobs[3];
    int fx_type;
    fp_mf3_run func_ptr;
    t_mf3_multi * mf3;
}t_per_audio_item_fx;

typedef struct
{
    int loaded;
    t_per_audio_item_fx * items[MK_PAIF_PER_ITEM];
}t_paif;

typedef struct
{
    t_wav_pool_item * wav_pool_item;  //pointer assigned when playing
    int wav_pool_uid;
    MKFLT ratio;
    int uid;
    int start_bar;
    double start_beat;
    double adjusted_start_beat;
    int timestretch_mode;  //tentatively: 0 == none, 1 == pitch, 2 == time+pitch
    MKFLT pitch_shift;
    MKFLT sample_start;
    MKFLT sample_end;
    int sample_start_offset;
    int sample_end_offset;
    //The audio track whose Modulex instance to write the samples to
    int outputs[MK_AUDIO_ITEM_SEND_COUNT];
    int sidechain[MK_AUDIO_ITEM_SEND_COUNT];
    MKFLT vols[MK_AUDIO_ITEM_SEND_COUNT];
    MKFLT vols_linear[MK_AUDIO_ITEM_SEND_COUNT];
    t_int_frac_read_head sample_read_heads[MK_AUDIO_ITEM_SEND_COUNT];
    t_adsr adsrs[MK_AUDIO_ITEM_SEND_COUNT];
    int is_linear_fade_in;
    int is_linear_fade_out;
    MKFLT fade_vols[MK_AUDIO_ITEM_SEND_COUNT];
    //fade smoothing
    t_state_variable_filter lp_filters[MK_AUDIO_ITEM_SEND_COUNT];

    int index;

    MKFLT timestretch_amt;
    MKFLT sample_fade_in;
    MKFLT sample_fade_out;
    int sample_fade_in_end;
    int sample_fade_out_start;
    MKFLT sample_fade_in_divisor;
    MKFLT sample_fade_out_divisor;

    t_pit_ratio pitch_ratio_ptr;

    MKFLT pitch_shift_end;
    MKFLT timestretch_amt_end;
    int is_reversed;
    MKFLT fadein_vol;
    MKFLT fadeout_vol;
    int paif_automation_uid;  //TODO:  This was never used, delete
    t_paif * paif;
} t_pydaw_audio_item __attribute__((aligned(16)));

typedef struct
{
    MKFLT sample_rate;
    int count;
    t_wav_pool_item items[PYDAW_MAX_WAV_POOL_ITEM_COUNT];
    char samples_folder[2048];  //This must be set when opening a project
}t_wav_pool;

typedef struct
{
    int item_num;
    int send_num;
}t_audio_item_index;

typedef struct
{
    t_pydaw_audio_item * items[PYDAW_MAX_AUDIO_ITEM_COUNT];
    t_audio_item_index indexes[DN_TRACK_COUNT][PYDAW_MAX_AUDIO_ITEM_COUNT];
    int index_counts[DN_TRACK_COUNT];
    int sample_rate;
    int uid;
} t_pydaw_audio_items;

t_pydaw_audio_item * g_pydaw_audio_item_get(MKFLT);
t_pydaw_audio_items * g_pydaw_audio_items_get(int);
void v_pydaw_audio_item_free(t_pydaw_audio_item *);
t_per_audio_item_fx * g_paif_get(MKFLT);

#ifdef	__cplusplus
}
#endif


t_per_audio_item_fx * g_paif_get(MKFLT a_sr)
{
    t_per_audio_item_fx * f_result;
    lmalloc((void**)&f_result, sizeof(t_per_audio_item_fx));

    int f_i = 0;
    while(f_i < 3)
    {
        f_result->a_knobs[f_i] = 64.0f;
        ++f_i;
    }
    f_result->fx_type = 0;
    f_result->func_ptr = v_mf3_run_off;
    f_result->mf3 = g_mf3_get(a_sr);

    return f_result;
}

t_paif * g_paif8_get()
{
    t_paif * f_result;
    lmalloc((void**)&f_result, sizeof(t_paif));

    int f_i;
    for(f_i = 0; f_i < MK_PAIF_PER_ITEM; ++f_i)
    {
        f_result->items[f_i] = NULL;
    }

    f_result->loaded = 0;

    return f_result;
}

void v_paif_free(t_paif * self)
{
    int f_i2;
    for(f_i2 = 0; f_i2 < MK_PAIF_PER_ITEM; ++f_i2)
    {
        if(self->items[f_i2])
        {
            v_mf3_free(self->items[f_i2]->mf3);
            free(self->items[f_i2]);
            self->items[f_i2] = 0;
        }
    }
}

void g_wav_pool_item_init(t_wav_pool_item *f_result,
    int a_uid, const char *a_path, MKFLT a_sr)
{
    f_result->uid = a_uid;
    f_result->is_loaded = 0;
    f_result->host_sr = a_sr;
    sprintf(f_result->path, "%s", a_path);
}

t_wav_pool_item * g_wav_pool_item_get(int a_uid, const char *a_path, MKFLT a_sr)
{
    t_wav_pool_item *f_result;

    lmalloc((void**)&f_result, sizeof(t_wav_pool_item));

    g_wav_pool_item_init(f_result, a_uid, a_path, a_sr);

    return f_result;
}

int i_wav_pool_item_load(t_wav_pool_item *a_wav_pool_item, int a_huge_pages)
{
    SF_INFO info;
    SNDFILE *file = NULL;
    size_t samples = 0;
    MKFLT *tmpFrames, *tmpSamples[2];
    int f_i = 0;

    info.format = 0;

    file = sf_open(a_wav_pool_item->path, SFM_READ, &info);

    if (!file)
    {
        printf("error: unable to load sample file '%s'\n",
            a_wav_pool_item->path);
        return 0;
    }

    samples = info.frames;

    tmpFrames = (MKFLT *)malloc(info.frames * info.channels * sizeof(MKFLT));
    mk_read_audio(file, tmpFrames, info.frames);
    sf_close(file);

    if ((int)(info.samplerate) != (int)(a_wav_pool_item->host_sr))
    {
	double ratio = (double)(info.samplerate) /
            (double)(a_wav_pool_item->host_sr);
        a_wav_pool_item->ratio_orig = (MKFLT)ratio;
    }
    else
    {
        a_wav_pool_item->ratio_orig = 1.0f;
    }

    int f_adjusted_channel_count = 1;
    if(info.channels >= 2)
    {
        f_adjusted_channel_count = 2;
    }

    int f_actual_array_size = (samples + PYDAW_AUDIO_ITEM_PADDING);
    f_i = 0;

    while(f_i < f_adjusted_channel_count)
    {
        if(a_huge_pages)
        {
            hpalloc((void**)&(tmpSamples[f_i]),
                f_actual_array_size * sizeof(MKFLT));
        }
        else
        {
            lmalloc((void**)&(tmpSamples[f_i]),
                f_actual_array_size * sizeof(MKFLT));
        }
        ++f_i;
    }

    int j;

    //For performing a 5ms fadeout of the sample, for preventing clicks
    MKFLT f_fade_out_dec = (1.0f / (MKFLT)(info.samplerate)) / (0.005);
    int f_fade_out_start = (samples + PYDAW_AUDIO_ITEM_PADDING_DIV2) -
        ((int)(0.005f * ((MKFLT)(info.samplerate))));
    MKFLT f_fade_out_envelope = 1.0f;
    MKFLT f_temp_sample = 0.0f;

    for(f_i = 0; f_i < f_actual_array_size; f_i++)
    {
        if((f_i > PYDAW_AUDIO_ITEM_PADDING_DIV2) &&
                (f_i < (samples + PYDAW_AUDIO_ITEM_PADDING_DIV2)))
        {
            if(f_i >= f_fade_out_start)
            {
                if(f_fade_out_envelope <= 0.0f)
                {
                    f_fade_out_dec = 0.0f;
                }

                f_fade_out_envelope -= f_fade_out_dec;
            }

	    for (j = 0; j < f_adjusted_channel_count; ++j)
            {
                f_temp_sample =
                        (tmpFrames[(f_i - PYDAW_AUDIO_ITEM_PADDING_DIV2) *
                        info.channels + j]);

                if(f_i >= f_fade_out_start)
                {
                    tmpSamples[j][f_i] = f_temp_sample * f_fade_out_envelope;
                }
                else
                {
                    tmpSamples[j][f_i] = f_temp_sample;
                }
            }
        }
        else
        {
            tmpSamples[0][f_i] = 0.0f;
            if(f_adjusted_channel_count > 1)
            {
                tmpSamples[1][f_i] = 0.0f;
            }
        }
    }

    free(tmpFrames);

    a_wav_pool_item->samples[0] = tmpSamples[0];

    if(f_adjusted_channel_count > 1)
    {
        a_wav_pool_item->samples[1] = tmpSamples[1];
    }
    else
    {
        a_wav_pool_item->samples[1] = 0;
    }

    //-20 to ensure we don't read past the end of the array
    a_wav_pool_item->length = (samples + PYDAW_AUDIO_ITEM_PADDING_DIV2 - 20);

    a_wav_pool_item->sample_rate = info.samplerate;

    a_wav_pool_item->channels = f_adjusted_channel_count;

    a_wav_pool_item->is_loaded = 1;

    return 1;
}

void v_wav_pool_item_free(t_wav_pool_item *a_wav_pool_item)
{
    a_wav_pool_item->path[0] = '\0';

    MKFLT *tmpOld[2];

    tmpOld[0] = a_wav_pool_item->samples[0];
    tmpOld[1] = a_wav_pool_item->samples[1];
    a_wav_pool_item->samples[0] = 0;
    a_wav_pool_item->samples[1] = 0;
    a_wav_pool_item->length = 0;

    if (tmpOld[0]) free(tmpOld[0]);
    if (tmpOld[1]) free(tmpOld[1]);
    free(a_wav_pool_item);
}

t_wav_pool * g_wav_pool_get(MKFLT a_sr)
{
    t_wav_pool * f_result;
    hpalloc((void**)&f_result, sizeof(t_wav_pool));

    f_result->sample_rate = a_sr;
    f_result->count = 0;

    int f_i = 0;
    while(f_i < PYDAW_MAX_WAV_POOL_ITEM_COUNT)
    {
        f_result->items[f_i].uid = -1;
        ++f_i;
    }
    return f_result;
}

void v_wav_pool_remove_item(t_wav_pool* a_wav_pool, int a_uid)
{
    if(USE_HUGEPAGES)
    {
        printf("Using hugepages, not freeing wav_pool uid %i\n", a_uid);
        return;
    }

    int f_i = 0;
    t_wav_pool_item * f_item = &a_wav_pool->items[a_uid];
    if(f_item->is_loaded)
    {
        f_item->is_loaded = 0;
        for(f_i = 0; f_i < f_item->channels; ++f_i)
        {
            MKFLT * f_data = f_item->samples[f_i];
            if(f_data)
            {
                free(f_data);
                printf("free'd %f MB\n",
                    ((MKFLT)f_item->length / (1024. * 1024.)) * 4.0);
                f_item->samples[f_i] = NULL;
            }
        }
    }
}

t_wav_pool_item * v_wav_pool_add_item(
    t_wav_pool* a_wav_pool, int a_uid, char * a_file_path)
{
    char f_path[2048];

    int f_pos = 2;

    if(a_file_path[0] != '/' && a_file_path[1] == ':')
    {
        char f_file_path[2048];

        f_file_path[0] = a_file_path[0];
        while(1)
        {
            f_file_path[f_pos - 1] = a_file_path[f_pos];
            if(a_file_path[f_pos] == '\0')
            {
                break;
            }
            ++f_pos;
        }

        printf("\nv_wav_pool_add_item:  '%s' '%s'\n",
            a_wav_pool->samples_folder, f_file_path);

        sprintf(f_path, "%s%s%s", a_wav_pool->samples_folder,
            PATH_SEP, f_file_path);
    }
    else
    {
        if(a_file_path[0] == '/')
        {
            sprintf(f_path, "%s%s", a_wav_pool->samples_folder, a_file_path);
        }
        else
        {
            sprintf(f_path, "%s%s%s", a_wav_pool->samples_folder,
                PATH_SEP, a_file_path);
        }
    }

    g_wav_pool_item_init(&a_wav_pool->items[a_uid], a_uid, f_path,
            a_wav_pool->sample_rate);
    ++a_wav_pool->count;
    return &a_wav_pool->items[a_uid];
}

/* Load entire pool at startup/open */
void v_wav_pool_add_items(t_wav_pool* a_wav_pool, char * a_file_path)
{
    a_wav_pool->count = 0;
    t_2d_char_array * f_arr = g_get_2d_array_from_file(a_file_path,
            PYDAW_LARGE_STRING);
    while(1)
    {
        v_iterate_2d_char_array(f_arr);
        if(f_arr->eof)
        {
            break;
        }
        int f_uid = atoi(f_arr->current_str);
        v_iterate_2d_char_array_to_next_line(f_arr);
        v_wav_pool_add_item(a_wav_pool, f_uid, f_arr->current_str);
    }
}

t_wav_pool_item * g_wav_pool_get_item_by_uid(t_wav_pool* a_wav_pool, int a_uid)
{
    if(a_wav_pool->items[a_uid].uid == a_uid)
    {
        if(!a_wav_pool->items[a_uid].is_loaded)
        {
            if(!i_wav_pool_item_load(&a_wav_pool->items[a_uid], 1))
            {
                printf("Failed to load file\n");
                return 0;
            }
        }
        return &a_wav_pool->items[a_uid];
    }
    else
    {
        printf("Couldn't find uid\n");
    }

    return 0;
}


void v_pydaw_audio_item_free(t_pydaw_audio_item* a_audio_item)
{
    //TODO:  Create a free method for these...
    //if(a_audio_item->adsr)
    //{ }
    //if(a_audio_item->sample_read_head)
    //{}
    if(!a_audio_item)
    {
        return;
    }

    if(a_audio_item->paif)
    {
        v_paif_free(a_audio_item->paif);
    }

    if(a_audio_item)
    {
        free(a_audio_item);
    }
}

t_pydaw_audio_item * g_pydaw_audio_item_get(MKFLT a_sr)
{
    int f_i;
    t_pydaw_audio_item * f_result;

    lmalloc((void**)&f_result, sizeof(t_pydaw_audio_item));

    f_result->ratio = 1.0f;
    f_result->paif = NULL;
    f_result->uid = -1;
    g_pit_ratio_init(&f_result->pitch_ratio_ptr);

    for(f_i = 0; f_i < MK_AUDIO_ITEM_SEND_COUNT; ++f_i)
    {
        g_adsr_init(&f_result->adsrs[f_i], a_sr);
        v_adsr_set_adsr(&f_result->adsrs[f_i], 0.003f, 0.1f, 1.0f, 0.2f);
        v_adsr_retrigger(&f_result->adsrs[f_i]);
        f_result->adsrs[f_i].stage = ADSR_STAGE_OFF;
        g_ifh_init(&f_result->sample_read_heads[f_i]);
        g_svf_init(&f_result->lp_filters[f_i], a_sr);
        v_svf_set_cutoff_base(&f_result->lp_filters[f_i],
            f_pit_hz_to_midi_note(7200.0f));
        v_svf_set_res(&f_result->lp_filters[f_i], -15.0f);
        v_svf_set_cutoff(&f_result->lp_filters[f_i]);
        f_result->vols[f_i] = 0.0f;
        f_result->vols_linear[f_i] = 1.0f;
    }

    return f_result;
}

t_pydaw_audio_items * g_pydaw_audio_items_get(int a_sr)
{
    t_pydaw_audio_items * f_result;

    lmalloc((void**)&f_result, sizeof(t_pydaw_audio_items));

    f_result->sample_rate = a_sr;

    int f_i, f_i2;

    for(f_i = 0; f_i < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i)
    {
        f_result->items[f_i] = 0; //g_pydaw_audio_item_get((MKFLT)(a_sr));
    }

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        f_result->index_counts[f_i] = 0;

        for(f_i2 = 0; f_i2 < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i2)
        {
            f_result->indexes[f_i][f_i2].item_num = 0;
            f_result->indexes[f_i][f_i2].send_num = 0;
        }
    }
    return f_result;
}

/* t_pydaw_audio_item * g_audio_item_load_single(MKFLT a_sr,
 * t_2d_char_array * f_current_string,
 * t_pydaw_audio_items * a_items)
 *
 */
t_pydaw_audio_item * g_audio_item_load_single(MKFLT a_sr,
        t_2d_char_array * f_current_string,
        t_pydaw_audio_items * a_items, t_wav_pool * a_wav_pool,
        t_wav_pool_item * a_wav_item)
{
    t_pydaw_audio_item * f_result;

    v_iterate_2d_char_array(f_current_string);

    if(f_current_string->eof)
    {
        return 0;
    }

    int f_index = atoi(f_current_string->current_str);

    if(a_items)
    {
        f_result = a_items->items[f_index];
    }
    else
    {
        f_result = g_pydaw_audio_item_get(a_sr);
    }

    f_result->index = f_index;

    v_iterate_2d_char_array(f_current_string);
    f_result->uid = atoi(f_current_string->current_str);

    if(a_wav_item)
    {
        f_result->wav_pool_item = a_wav_item;
    }
    else
    {
        f_result->wav_pool_item =
            g_wav_pool_get_item_by_uid(a_wav_pool, f_result->uid);

        if(!f_result->wav_pool_item)
        {
            printf("####################\n\n");
            printf("ERROR:  g_audio_item_load_single failed for uid %i, "
                    "not found\n\n", f_result->uid);
            printf("####################\n\n");
            return 0;
        }
    }
    v_iterate_2d_char_array(f_current_string);
    MKFLT f_sample_start = atof(f_current_string->current_str) * 0.001f;

    if(f_sample_start < 0.0f)
    {
        f_sample_start = 0.0f;
    }
    else if(f_sample_start > 0.999f)
    {
        f_sample_start = 0.999f;
    }

    f_result->sample_start = f_sample_start;

    f_result->sample_start_offset =
            (int)((f_result->sample_start *
            ((MKFLT)f_result->wav_pool_item->length))) +
            PYDAW_AUDIO_ITEM_PADDING_DIV2;

    v_iterate_2d_char_array(f_current_string);
    MKFLT f_sample_end = atof(f_current_string->current_str) * 0.001f;

    if(f_sample_end < 0.001f)
    {
        f_sample_end = 0.001f;
    }
    else if(f_sample_end > 1.0f)
    {
        f_sample_end = 1.0f;
    }

    f_result->sample_end = f_sample_end;

    f_result->sample_end_offset = (int)((f_result->sample_end *
            ((MKFLT)f_result->wav_pool_item->length)));

    v_iterate_2d_char_array(f_current_string);
    f_result->start_bar = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->start_beat = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_mode = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->pitch_shift = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[0] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[0] = atof(f_current_string->current_str);
    f_result->vols_linear[0] = f_db_to_linear_fast(f_result->vols[0]);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_amt = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sample_fade_in = atof(f_current_string->current_str) * 0.001f;

    v_iterate_2d_char_array(f_current_string);
    f_result->sample_fade_out = atof(f_current_string->current_str) * 0.001f;

    //lane, not used by the back-end
    v_iterate_2d_char_array(f_current_string);


    v_iterate_2d_char_array(f_current_string);
    f_result->pitch_shift_end = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->timestretch_amt_end = atof(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->is_reversed = atoi(f_current_string->current_str);

    //crispness, Not used in the back-end
    v_iterate_2d_char_array(f_current_string);

    //These are multiplied by -1.0f to work correctly with
    //v_pydaw_audio_item_set_fade_vol()
    v_iterate_2d_char_array(f_current_string);
    f_result->fadein_vol = atof(f_current_string->current_str) * -1.0f;

    v_iterate_2d_char_array(f_current_string);
    f_result->fadeout_vol = atof(f_current_string->current_str) * -1.0f;

    v_iterate_2d_char_array(f_current_string);
    f_result->paif_automation_uid = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[1] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[1] = atof(f_current_string->current_str);
    f_result->vols_linear[1] = f_db_to_linear_fast(f_result->vols[1]);

    v_iterate_2d_char_array(f_current_string);
    f_result->outputs[2] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->vols[2] = atof(f_current_string->current_str);
    f_result->vols_linear[2] = f_db_to_linear_fast(f_result->vols[2]);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[0] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[1] = atoi(f_current_string->current_str);

    v_iterate_2d_char_array(f_current_string);
    f_result->sidechain[2] = atoi(f_current_string->current_str);

    if(f_result->sample_start_offset < PYDAW_AUDIO_ITEM_PADDING_DIV2)
    {
        printf("f_result->sample_start_offset <= PYDAW_AUDIO_ITEM_PADDING_DIV2"
                " %i %i\n", f_result->sample_start_offset,
                PYDAW_AUDIO_ITEM_PADDING_DIV2);
        f_result->sample_start_offset = PYDAW_AUDIO_ITEM_PADDING_DIV2;
    }

    if(f_result->sample_end_offset < PYDAW_AUDIO_ITEM_PADDING_DIV2)
    {
        printf("f_result->sample_end_offset <= PYDAW_AUDIO_ITEM_PADDING_DIV2"
                " %i %i\n", f_result->sample_end_offset,
                PYDAW_AUDIO_ITEM_PADDING_DIV2);
        f_result->sample_end_offset = PYDAW_AUDIO_ITEM_PADDING_DIV2;
    }

    if(f_result->sample_start_offset > f_result->wav_pool_item->length)
    {
        printf("f_result->sample_start_offset >= "
                "f_result->wav_pool_item->length %i %i\n",
                f_result->sample_start_offset, f_result->wav_pool_item->length);
        f_result->sample_start_offset = f_result->wav_pool_item->length;
    }

    if(f_result->sample_end_offset > f_result->wav_pool_item->length)
    {
        printf("f_result->sample_end_offset >= f_result->wav_pool_item->length"
                " %i %i\n", f_result->sample_end_offset,
                f_result->wav_pool_item->length);
        f_result->sample_end_offset = f_result->wav_pool_item->length;
    }

    if(f_result->is_reversed)
    {
        int f_old_start = f_result->sample_start_offset;
        int f_old_end = f_result->sample_end_offset;
        f_result->sample_start_offset =
                f_result->wav_pool_item->length - f_old_end;
        f_result->sample_end_offset =
                f_result->wav_pool_item->length - f_old_start;
    }

    f_result->sample_fade_in_end =
            f_result->sample_end_offset - f_result->sample_start_offset;
    f_result->sample_fade_in_end =
            f_result->sample_start_offset +
            ((int)((MKFLT)(f_result->sample_fade_in_end) *
            f_result->sample_fade_in)) + PYDAW_AUDIO_ITEM_PADDING_DIV2;

    // Anything less than this will use a linear fade
    int max_linear = f_result->wav_pool_item->sample_rate / 10;

    if(f_result->sample_fade_in_end < max_linear)
    {
        f_result->is_linear_fade_in = 1;
    }
    else
    {
        printf("Non-linear fade in\n");
        f_result->is_linear_fade_in = 0;
    }

    f_result->sample_fade_out_start =
            f_result->sample_end_offset - f_result->sample_start_offset;
    f_result->sample_fade_out_start =
            f_result->sample_start_offset +
            ((int)((MKFLT)(f_result->sample_fade_out_start) *
            f_result->sample_fade_out)) + PYDAW_AUDIO_ITEM_PADDING_DIV2;

    int f_fade_diff = (f_result->sample_fade_in_end -
        f_result->sample_start_offset - (PYDAW_AUDIO_ITEM_PADDING_DIV2));

    if(f_fade_diff > 0)
    {
        f_result->sample_fade_in_divisor = 1.0f / (MKFLT)f_fade_diff;
    }
    else
    {
        f_result->sample_fade_in_divisor = 0.0f;
    }

    f_fade_diff =
        (f_result->sample_end_offset - f_result->sample_fade_out_start);

    if(f_fade_diff < max_linear)
    {
        f_result->is_linear_fade_out = 1;
    }
    else
    {
        printf("Non-linear fade out\n");
        f_result->is_linear_fade_out = 0;
    }

    if(f_fade_diff > 0)
    {
        f_result->sample_fade_out_divisor = 1.0f / (MKFLT)f_fade_diff;
    }
    else
    {
        f_result->sample_fade_out_divisor = 0.0f;
    }

    f_result->adjusted_start_beat =
            ((MKFLT)f_result->start_bar * 4) + f_result->start_beat;

    if(f_result->is_reversed)
    {
        f_result->sample_fade_in_end =
                f_result->sample_end_offset - (f_result->sample_fade_in_end -
                f_result->sample_start_offset);
        f_result->sample_fade_out_start =
                f_result->sample_start_offset + (f_result->sample_end_offset -
                f_result->sample_fade_out_start);
    }

    f_result->ratio = f_result->wav_pool_item->ratio_orig;

    switch(f_result->timestretch_mode)
    {
        //case 0:  //None
        //    break;
        case 1:  //Pitch affecting time
        {
            //Otherwise, it's already been stretched offline
            if(f_result->pitch_shift == f_result->pitch_shift_end)
            {
                if((f_result->pitch_shift) >= 0.0f)
                {
                    f_result->ratio *=
                            f_pit_midi_note_to_ratio_fast(0.0f,
                                (f_result->pitch_shift),
                                &f_result->pitch_ratio_ptr);
                }
                else
                {
                    f_result->ratio *=
                            f_pit_midi_note_to_ratio_fast(
                            ((f_result->pitch_shift) * -1.0f),
                            0.0f,
                            &f_result->pitch_ratio_ptr);
                }
            }
        }
            break;
        case 2:  //Time affecting pitch
        {
            //Otherwise, it's already been stretched offline
            if(f_result->timestretch_amt == f_result->timestretch_amt_end)
            {
                f_result->ratio *= (1.0f / (f_result->timestretch_amt));
            }
        }
            break;
        /*
        //Don't have to do anything with these, they comes pre-stretched...
        case 3:  //Rubberband
        case 4:  //Rubberband (preserving formants)
        case 5:  //SBSMS
        case 6: Paulstretch
        */
    }

    return f_result;
}

void v_pydaw_audio_item_set_fade_vol(t_pydaw_audio_item *self,
        int a_send_num)
{
    t_int_frac_read_head * read_head =
        &self->sample_read_heads[a_send_num];

    if(self->is_reversed)
    {
        if(read_head->whole_number > self->sample_fade_in_end &&
           self->sample_fade_in_divisor != 0.0f)
        {
            self->fade_vols[a_send_num] =
                ((MKFLT)(self->sample_read_heads[a_send_num].whole_number) -
                self->sample_fade_in_end - PYDAW_AUDIO_ITEM_PADDING_DIV2)
                * self->sample_fade_in_divisor;

            if(self->is_linear_fade_in)
            {
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            }
            else
            {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num]) * self->fadein_vol)
                    - self->fadein_vol;
                //self->fade_vol = (self->fade_vol * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
            }
        }
        else if(read_head->whole_number <= self->sample_fade_out_start &&
                self->sample_fade_out_divisor != 0.0f)
        {
            self->fade_vols[a_send_num] =
                ((MKFLT)(self->sample_fade_out_start - read_head->whole_number))
                * self->sample_fade_out_divisor;

            if(self->is_linear_fade_out)
            {
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            }
            else
            {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num])
                    * self->fadeout_vol) - self->fadeout_vol;
                //self->fade_vol =
                //  ((self->fade_vol) * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
            }
        }
        else
        {
            self->fade_vols[a_send_num] = 1.0f;
        }
    }
    else
    {
        if(read_head->whole_number < self->sample_fade_in_end &&
           self->sample_fade_in_divisor != 0.0f)
        {
            self->fade_vols[a_send_num] =
                ((MKFLT)(self->sample_fade_in_end -
                read_head->whole_number - PYDAW_AUDIO_ITEM_PADDING_DIV2))
                * self->sample_fade_in_divisor;

            if(self->is_linear_fade_in)
            {
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            }
            else
            {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num])
                    * self->fadein_vol) - self->fadein_vol;
                //self->fade_vol =
                //  ((self->fade_vol) * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
                self->fade_vols[a_send_num] =
                    v_svf_run_2_pole_lp(&self->lp_filters[a_send_num],
                    self->fade_vols[a_send_num]);
            }
        }
        else if(read_head->whole_number >= self->sample_fade_out_start &&
                self->sample_fade_out_divisor != 0.0f)
        {
            self->fade_vols[a_send_num] =
                ((MKFLT)(self->sample_read_heads[a_send_num].whole_number -
                self->sample_fade_out_start)) * self->sample_fade_out_divisor;

            if(self->is_linear_fade_out)
            {
                self->fade_vols[a_send_num] =
                    1.0f - self->fade_vols[a_send_num];
            }
            else
            {
                self->fade_vols[a_send_num] =
                    ((1.0f - self->fade_vols[a_send_num]) *
                    self->fadeout_vol) - self->fadeout_vol;
                //self->fade_vol = (self->fade_vol * 40.0f) - 40.0f;
                self->fade_vols[a_send_num] =
                    f_db_to_linear_fast(self->fade_vols[a_send_num]);
                self->fade_vols[a_send_num] =
                    v_svf_run_2_pole_lp(&self->lp_filters[a_send_num],
                    self->fade_vols[a_send_num]);
            }
        }
        else
        {
            self->fade_vols[a_send_num] = 1.0f;
        }
    }
}

void v_pydaw_audio_items_free(t_pydaw_audio_items *a_audio_items)
{
    int f_i;
    for(f_i = 0; f_i < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i)
    {
        v_pydaw_audio_item_free(a_audio_items->items[f_i]);
        a_audio_items->items[f_i] = NULL;
    }

    free(a_audio_items);
}



#endif	/* PYDAW_AUDIO_TRACKS_H */

