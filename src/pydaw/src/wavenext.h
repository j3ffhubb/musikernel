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

#ifndef WAVENEXT_H
#define	WAVENEXT_H

#include "musikernel.h"

#define WN_CONFIGURE_KEY_LOAD_AB_OPEN "abo"
#define WN_CONFIGURE_KEY_WE_SET "we"
#define WN_CONFIGURE_KEY_WE_EXPORT "wex"
#define WN_CONFIGURE_KEY_WN_PLAYBACK "wnp"
#define WN_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define WN_CONFIGURE_KEY_AUDIO_INPUTS "ai"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    t_wav_pool_item * ab_wav_item;
    t_pydaw_audio_item * ab_audio_item;
    t_pytrack * track_pool[1];
    char * tracks_folder;
    char * project_folder;
}t_wavenext;

void v_pydaw_set_ab_mode(int a_mode);
void v_pydaw_set_we_file(t_wavenext * self, const char * a_file);
void v_pydaw_set_wave_editor_item(t_wavenext * self, const char * a_string);
inline void v_pydaw_run_wave_editor(int sample_count,
    float **output, float * a_input);

#ifdef	__cplusplus
}
#endif

t_wavenext * wavenext;

void g_wavenext_get()
{
    float f_sample_rate = musikernel->thread_storage[0].sample_rate;
    clalloc((void**)&wavenext, sizeof(t_wavenext));
    wavenext->ab_wav_item = 0;
    wavenext->ab_audio_item = g_pydaw_audio_item_get(f_sample_rate);
    wavenext->tracks_folder = (char*)malloc(sizeof(char) * 1024);
    wavenext->project_folder = (char*)malloc(sizeof(char) * 1024);
    int f_i = 0;
    while(f_i < 1)
    {
        wavenext->track_pool[f_i] = g_pytrack_get(f_i, f_sample_rate);
        ++f_i;
    }
}

void v_wn_set_playback_mode(t_wavenext * self, int a_mode, int a_lock)
{
    switch(a_mode)
    {
        case 0: //stop
        {
            int f_old_mode = musikernel->playback_mode;

            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }

            if(f_old_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                v_stop_record_audio();
            }
        }
            break;
        case 1:  //play
        {
            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            if(wavenext->ab_wav_item)
            {
                v_ifh_retrigger(
                    &wavenext->ab_audio_item->sample_read_heads[0],
                    wavenext->ab_audio_item->sample_start_offset);
                v_adsr_retrigger(&wavenext->ab_audio_item->adsrs[0]);
                v_svf_reset(&wavenext->ab_audio_item->lp_filters[0]);
            }

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

            v_prepare_to_record_audio();

            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }
            break;
        default:
            assert(0);
            break;
    }
}

void v_pydaw_we_export(t_wavenext * self, const char * a_file_out)
{
    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 1;
    pthread_spin_unlock(&musikernel->main_lock);

    float f_sample_rate = musikernel->thread_storage[0].sample_rate;

    long f_size = 0;
    long f_block_size = (musikernel->sample_count);

    float * f_output = NULL;
    lmalloc((void**)&f_output, sizeof(float) * (f_block_size * 2));

    float ** f_buffer = NULL;
    lmalloc((void**)&f_buffer, sizeof(float*) * 2);

    int f_i = 0;
    while(f_i < 2)
    {
        lmalloc((void**)&f_buffer[f_i], sizeof(float) * f_block_size);
        ++f_i;
    }

    v_wn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_PLAY, 0);

    printf("\nOpening SNDFILE with sample rate %f\n", f_sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(f_sample_rate);

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    printf("\nSuccessfully opened SNDFILE\n\n");

#ifdef __linux__
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    while((self->ab_audio_item->sample_read_heads[0].whole_number) <
            (self->ab_audio_item->sample_end_offset))
    {
        int f_i = 0;
        f_size = 0;

        while(f_i < f_block_size)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
            ++f_i;
        }

        v_pydaw_run_wave_editor(f_block_size, f_buffer, NULL);

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

        sf_writef_float(f_sndfile, f_output, f_block_size);
    }

#ifdef __linux__

    clock_gettime(CLOCK_REALTIME, &f_finish);

    v_pydaw_print_benchmark("v_pydaw_offline_render ", f_start, f_finish);
    printf("f_size = %ld\n", f_size);

#endif

    v_wn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_OFF, 0);

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_output);

    char f_tmp_finished[1024];

    sprintf(f_tmp_finished, "%s.finished", a_file_out);

    v_pydaw_write_to_file(f_tmp_finished, "finished");

    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 0;
    pthread_spin_unlock(&musikernel->main_lock);

#ifdef __linux__
    chown_file(a_file_out);
#endif

}


void v_pydaw_set_we_file(t_wavenext * self, const char * a_uid)
{
    int uid = atoi(a_uid);

    t_wav_pool_item * f_result = g_wav_pool_get_item_by_uid(
        musikernel->wav_pool, uid);

    if(f_result->is_loaded || i_wav_pool_item_load(f_result, 1))
    {
        pthread_spin_lock(&musikernel->main_lock);

        self->ab_wav_item = f_result;

        self->ab_audio_item->ratio = self->ab_wav_item->ratio_orig;

        pthread_spin_unlock(&musikernel->main_lock);
    }
    else
    {
        printf("i_wav_pool_item_load failed in v_pydaw_set_we_file\n");
    }
}

void v_wn_open_tracks()
{
    v_pydaw_open_track(wavenext->track_pool[0], wavenext->tracks_folder, 0);
}

void v_wn_open_project()
{
    sprintf(wavenext->project_folder, "%s%sprojects%swavenext",
        musikernel->project_folder, PATH_SEP, PATH_SEP);

    sprintf(wavenext->tracks_folder, "%s%stracks",
        wavenext->project_folder, PATH_SEP);
    v_wn_open_tracks();
}

void v_pydaw_set_wave_editor_item(t_wavenext * self,
        const char * a_val)
{
    t_2d_char_array * f_current_string = g_get_2d_array(PYDAW_MEDIUM_STRING);
    sprintf(f_current_string->array, "%s", a_val);
    t_pydaw_audio_item * f_old = self->ab_audio_item;
    t_pydaw_audio_item * f_result = g_audio_item_load_single(
            musikernel->thread_storage[0].sample_rate, f_current_string, 0, 0,
            self->ab_wav_item);

    pthread_spin_lock(&musikernel->main_lock);
    self->ab_audio_item = f_result;
    pthread_spin_unlock(&musikernel->main_lock);

    g_free_2d_char_array(f_current_string);
    if(f_old)
    {
        v_pydaw_audio_item_free(f_old);
    }
}


inline void v_pydaw_run_wave_editor(int sample_count,
        float **output, float * a_input)
{
    t_wavenext * self = wavenext;
    t_pydaw_plugin * f_plugin;

    int f_global_track_num = 0;
    t_pytrack * f_track = self->track_pool[f_global_track_num];
    register int f_i;

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = 0.0f;
        output[1][f_i] = 0.0f;
    }

    if(a_input)
    {
        for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            v_audio_input_run(f_i, output, NULL, a_input, sample_count, NULL);
        }
    }

    if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_PLAY)
    {
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            if((self->ab_audio_item->sample_read_heads[0].whole_number) <
                (self->ab_audio_item->sample_end_offset))
            {
                v_adsr_run(&self->ab_audio_item->adsrs[0]);
                v_pydaw_audio_item_set_fade_vol(self->ab_audio_item, 0);

                if(self->ab_wav_item->channels == 1)
                {
                    float f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                    (self->ab_wav_item->samples[0]),
                    (self->ab_audio_item->sample_read_heads[0].whole_number),
                    (self->ab_audio_item->sample_read_heads[0].fraction)) *
                    (self->ab_audio_item->adsrs[0].output) *
                    (self->ab_audio_item->vols_linear[0]) *
                    (self->ab_audio_item->fade_vols[0]);

                    output[0][f_i] = f_tmp_sample;
                    output[1][f_i] = f_tmp_sample;
                }
                else if(self->ab_wav_item->channels > 1)
                {
                    output[0][f_i] = f_cubic_interpolate_ptr_ifh(
                    (self->ab_wav_item->samples[0]),
                    (self->ab_audio_item->sample_read_heads[0].whole_number),
                    (self->ab_audio_item->sample_read_heads[0].fraction)) *
                    (self->ab_audio_item->adsrs[0].output) *
                    (self->ab_audio_item->vols_linear[0]) *
                    (self->ab_audio_item->fade_vols[0]);

                    output[1][f_i] = f_cubic_interpolate_ptr_ifh(
                    (self->ab_wav_item->samples[1]),
                    (self->ab_audio_item->sample_read_heads[0].whole_number),
                    (self->ab_audio_item->sample_read_heads[0].fraction)) *
                    (self->ab_audio_item->adsrs[0].output) *
                    (self->ab_audio_item->vols_linear[0]) *
                    (self->ab_audio_item->fade_vols[0]);
                }

                v_ifh_run(&self->ab_audio_item->sample_read_heads[0],
                        self->ab_audio_item->ratio);

                if(musikernel->playback_mode != PYDAW_PLAYBACK_MODE_PLAY &&
                    self->ab_audio_item->adsrs[0].stage < ADSR_STAGE_RELEASE)
                {
                    v_adsr_release(&self->ab_audio_item->adsrs[0]);
                }
            }
        }
    }

    float ** f_buff = f_track->buffers;

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        f_buff[0][f_i] = output[0][f_i];
        f_buff[1][f_i] = output[1][f_i];
    }

    for(f_i = 0; f_i < MAX_PLUGIN_COUNT; ++f_i)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin && f_plugin->power)
        {
            f_plugin->descriptor->run_replacing(
                f_plugin->PYFX_handle, sample_count, f_track->event_list,
                f_plugin->atm_list);
        }
    }

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = f_buff[0][f_i];
        output[1][f_i] = f_buff[1][f_i];
    }

    v_pkm_run(f_track->peak_meter, f_buff[0], f_buff[1],
        musikernel->sample_count);
}

void v_wn_osc_send(t_osc_send_data * a_buffers)
{
    int f_i;

    f_i = 0;
    t_pkm_peak_meter * f_pkm = wavenext->track_pool[0]->peak_meter;
    sprintf(a_buffers->f_tmp1, "%i:%f:%f",
        f_i, f_pkm->value[0], f_pkm->value[1]);
    v_pkm_reset(f_pkm);

    v_queue_osc_message("peak", a_buffers->f_tmp1);

    if(musikernel->playback_mode == 1)
    {
        float f_frac =
        (float)(wavenext->ab_audio_item->sample_read_heads[
            0].whole_number)
        / (float)(wavenext->ab_audio_item->wav_pool_item->length);

        sprintf(a_buffers->f_msg, "%f", f_frac);
        v_queue_osc_message("wec", a_buffers->f_msg);
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
            v_ui_send("musikernel/wavenext", a_buffers->f_tmp1);
        }
    }
}

void v_wn_update_audio_inputs()
{
    v_pydaw_update_audio_inputs(wavenext->project_folder);
}

void v_wn_configure(const char* a_key, const char* a_value)
{
    printf("v_wn_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, WN_CONFIGURE_KEY_LOAD_AB_OPEN))
    {
        v_pydaw_set_we_file(wavenext, a_value);
    }
    else if(!strcmp(a_key, WN_CONFIGURE_KEY_AUDIO_INPUTS))
    {
        v_wn_update_audio_inputs();
    }
    else if(!strcmp(a_key, WN_CONFIGURE_KEY_WE_SET))
    {
        v_pydaw_set_wave_editor_item(wavenext, a_value);
    }
    else if(!strcmp(a_key, WN_CONFIGURE_KEY_WE_EXPORT))
    {
        v_pydaw_we_export(wavenext, a_value);
    }
    else if(!strcmp(a_key, WN_CONFIGURE_KEY_WN_PLAYBACK))
    {
        int f_mode = atoi(a_value);
        assert(f_mode >= 0 && f_mode <= 2);
        v_wn_set_playback_mode(wavenext, f_mode, 1);
    }
    else if(!strcmp(a_key, WN_CONFIGURE_KEY_PLUGIN_INDEX))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 5,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_plugin_index = atoi(f_val_arr->array[2]);
        int f_plugin_uid = atoi(f_val_arr->array[3]);
        int f_power = atoi(f_val_arr->array[4]);

        t_pytrack * f_track = wavenext->track_pool[f_track_num];

        v_pydaw_set_plugin_index(
            f_track, f_index, f_plugin_index, f_plugin_uid, f_power, 1);

        g_free_1d_char_array(f_val_arr);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }
}

void v_wn_test()
{
    printf("Begin Wave-Next test\n");

    musikernel->sample_count = 512;

    v_pydaw_set_host(MK_HOST_WAVENEXT);
    v_wn_set_playback_mode(wavenext, PYDAW_PLAYBACK_MODE_REC, 0);
    float * f_output_arr[2];

    int f_i, f_i2;

    for(f_i = 0; f_i < 2; ++f_i)
    {
        hpalloc((void**)&f_output_arr[f_i], sizeof(float) * 1024);

        for(f_i2 = 0; f_i2 < 1024; ++f_i2)
        {
            f_output_arr[f_i][f_i2] = 0.0f;
        }
    }

    float * f_input_arr;
    hpalloc((void**)&f_input_arr, sizeof(float) * (1024 * 1024));

    for(f_i = 0; f_i < (1024 * 1024); ++f_i)
    {
        f_input_arr[f_i] = 0.0f;
    }

    for(f_i = 0; f_i < 100000; ++f_i)
    {
        v_pydaw_run_wave_editor(512, f_output_arr, f_input_arr);
    }

    v_wn_set_playback_mode(wavenext, PYDAW_PLAYBACK_MODE_OFF, 0);

    printf("End Wave-Next test\n");
}

#endif	/* WAVENEXT_H */

