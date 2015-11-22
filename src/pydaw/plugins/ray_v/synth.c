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


#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"
#include "../../libmodsynth/lib/amp.h"
#include "../../libmodsynth/modules/filter/svf.h"
#include "../../libmodsynth/lib/lms_math.h"
#include "synth.h"


static void v_run_rayv_voice(t_rayv *p, t_voc_single_voice * a_poly_voice,
        t_rayv_poly_voice *d, PYFX_Data *out0, PYFX_Data *out1, int a_i);

static void v_cleanup_rayv(PYFX_Handle instance)
{
    free(instance);
}

static void v_rayv_or_prep(PYFX_Handle instance)
{
    t_rayv *plugin = (t_rayv *)instance;
    int f_i2 = 0;
    register int f_i;
    while(f_i2 < RAYV_POLYPHONY)
    {
        t_rayv_poly_voice * f_voice = plugin->data[f_i2];
        f_i = 0;
        while(f_i < 1000000)
        {
            f_osc_run_unison_osc_core_only(&f_voice->osc_unison1);
            f_osc_run_unison_osc_core_only(&f_voice->osc_unison2);
            ++f_i;
        }
        ++f_i2;
    }
}

static void v_rayv_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_rayv *plugin = (t_rayv *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void rayvPanic(PYFX_Handle instance)
{
    t_rayv *plugin = (t_rayv *)instance;
    int f_i = 0;
    while(f_i < RAYV_POLYPHONY)
    {
        v_adsr_kill(&plugin->data[f_i]->adsr_amp);
        ++f_i;
    }
}

static void v_rayv_on_stop(PYFX_Handle instance)
{
    t_rayv *plugin = (t_rayv *)instance;
    int f_i = 0;
    while(f_i < RAYV_POLYPHONY)
    {
        v_rayv_poly_note_off(plugin->data[f_i], 0);
        ++f_i;
    }
    plugin->sv_pitch_bend_value = 0.0f;
}

static void v_rayv_connect_buffer(PYFX_Handle instance, int a_index,
        float * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }

    t_rayv *plugin = (t_rayv*)instance;

    switch(a_index)
    {
        case 0:
            plugin->output0 = DataLocation;
            break;
        case 1:
            plugin->output1 = DataLocation;
            break;
        default:
            assert(0);
            break;
    }
}

static void v_rayv_connect_port(PYFX_Handle instance, int port,
			  PYFX_Data * data)
{
    t_rayv *plugin;

    plugin = (t_rayv *) instance;

    switch (port)
    {
        case RAYV_ATTACK:
            plugin->attack = data;
            break;
        case RAYV_DECAY:
            plugin->decay = data;
            break;
        case RAYV_SUSTAIN:
            plugin->sustain = data;
            break;
        case RAYV_RELEASE:
            plugin->release = data;
            break;
        case RAYV_TIMBRE:
            plugin->timbre = data;
            break;
        case RAYV_RES:
            plugin->res = data;
            break;
        case RAYV_DIST:
            plugin->dist = data;
            break;
        case RAYV_FILTER_ATTACK:
            plugin->attack_f = data;
            break;
        case RAYV_FILTER_DECAY:
            plugin->decay_f = data;
            break;
        case RAYV_FILTER_SUSTAIN:
            plugin->sustain_f = data;
            break;
        case RAYV_FILTER_RELEASE:
            plugin->release_f = data;
            break;
        case RAYV_NOISE_AMP:
            plugin->noise_amp = data;
            break;
        case RAYV_DIST_WET:
            plugin->dist_wet = data;
            break;
        case RAYV_FILTER_ENV_AMT:
            plugin->filter_env_amt = data;
            break;
        case RAYV_MASTER_VOLUME:
            plugin->master_vol = data;
            break;
        case RAYV_OSC1_PITCH:
            plugin->osc1pitch = data;
            break;
        case RAYV_OSC1_TUNE:
            plugin->osc1tune = data;
            break;
        case RAYV_OSC1_TYPE:
            plugin->osc1type = data;
            break;
        case RAYV_OSC1_VOLUME:
            plugin->osc1vol = data;
            break;
        case RAYV_OSC2_PITCH:
            plugin->osc2pitch = data;
            break;
        case RAYV_OSC2_TUNE:
            plugin->osc2tune = data;
            break;
        case RAYV_OSC2_TYPE:
            plugin->osc2type = data;
            break;
        case RAYV_OSC2_VOLUME:
            plugin->osc2vol = data;
            break;
        case RAYV_MASTER_UNISON_VOICES:
            plugin->master_uni_voice = data;
            break;
        case RAYV_MASTER_UNISON_SPREAD:
            plugin->master_uni_spread = data;
            break;
        case RAYV_MASTER_GLIDE:
            plugin->master_glide = data;
            break;
        case RAYV_MASTER_PITCHBEND_AMT:
            plugin->master_pb_amt = data;
            break;
        case RAYV_PITCH_ENV_AMT:
            plugin->pitch_env_amt = data;
            break;
        case RAYV_PITCH_ENV_TIME:
            plugin->pitch_env_time = data;
            break;
        case RAYV_LFO_FREQ:
            plugin->lfo_freq = data;
            break;
        case RAYV_LFO_TYPE:
            plugin->lfo_type = data;
            break;
        case RAYV_LFO_AMP:
            plugin->lfo_amp = data;
            break;
        case RAYV_LFO_PITCH:
            plugin->lfo_pitch = data;
            break;
        case RAYV_LFO_FILTER:
            plugin->lfo_filter = data;
            break;
        case RAYV_OSC_HARD_SYNC:
            plugin->sync_hard = data;
            break;
        case RAYV_RAMP_CURVE:
            plugin->ramp_curve = data;
            break;
        case RAYV_FILTER_KEYTRK:
            plugin->filter_keytrk = data;
            break;
        case RAYV_MONO_MODE:
            plugin->mono_mode = data;
            break;
        case RAYV_LFO_PHASE:
            plugin->lfo_phase = data;
            break;
        case RAYV_LFO_PITCH_FINE:
            plugin->lfo_pitch_fine = data;
            break;
        case RAYV_ADSR_PREFX:
            plugin->adsr_prefx = data;
            break;
        case RAYV_MIN_NOTE:
            plugin->min_note = data;
            break;
        case RAYV_MAX_NOTE:
            plugin->max_note = data;
            break;
        case RAYV_MASTER_PITCH:
            plugin->master_pitch = data;
            break;
        case RAYV_ADSR_LIN_MAIN: plugin->adsr_lin_main = data; break;
    }
}

static PYFX_Handle g_rayv_instantiate(PYFX_Descriptor * descriptor,
        int a_sr, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_rayv *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_rayv));

    plugin_data->fs = a_sr;

    int f_i;

    plugin_data->voices = g_voc_get_voices(RAYV_POLYPHONY,
            RAYV_POLYPHONY_THRESH);

    for (f_i = 0; f_i < RAYV_POLYPHONY; ++f_i)
    {
        plugin_data->data[f_i] = g_rayv_poly_init(a_sr);
        plugin_data->data[f_i]->note_f = f_i;
    }

    plugin_data->sampleNo = 0;

    plugin_data->sv_pitch_bend_value = 0.0f;
    plugin_data->sv_last_note = -1.0f;  //For glide

    //initialize all monophonic modules
    plugin_data->mono_modules = v_rayv_mono_init(plugin_data->fs);

    plugin_data->port_table = g_pydaw_get_port_table(
        (void**)plugin_data, descriptor);
    plugin_data->descriptor = descriptor;

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}


static void v_rayv_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_rayv *plugin_data = (t_rayv*)instance;
    pydaw_generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_rayv_set_port_value(PYFX_Handle Instance,
        int a_port, float a_value)
{
    t_rayv *plugin_data = (t_rayv*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static void v_rayv_process_midi_event(
    t_rayv * plugin_data, t_pydaw_seq_event * a_event, int f_poly_mode)
{
    int f_min_note = (int)*plugin_data->min_note;
    int f_max_note = (int)*plugin_data->max_note;

    if (a_event->type == PYDAW_EVENT_NOTEON)
    {
        if (a_event->velocity > 0)
        {
            if(a_event->note > f_max_note ||
                a_event->note < f_min_note)
            {
                return;
            }
            int f_voice = i_pick_voice(plugin_data->voices,
                     a_event->note,
                     plugin_data->sampleNo,
                     a_event->tick);

            int f_adsr_main_lin = (int)(*plugin_data->adsr_lin_main);
            plugin_data->data[f_voice]->adsr_run_func =
                FP_ADSR_RUN[f_adsr_main_lin];

            plugin_data->data[f_voice]->amp =
                    f_db_to_linear_fast(
                    //-20db to 0db, + master volume (0 to -60)
                    ((a_event->velocity * 0.094488) - 12.0f));
            v_svf_velocity_mod(&plugin_data->data[f_voice]->svf_filter,
                    a_event->velocity);

            float f_master_pitch = (*plugin_data->master_pitch);

            plugin_data->data[f_voice]->note_f =
                    (float)a_event->note + f_master_pitch;
            plugin_data->data[f_voice]->note =
                    a_event->note + (int)(f_master_pitch);

            plugin_data->data[f_voice]->filter_keytrk =
                    (*plugin_data->filter_keytrk) * 0.01f *
                    (plugin_data->data[f_voice]->note_f);

            plugin_data->data[f_voice]->target_pitch =
                    (plugin_data->data[f_voice]->note_f);

            if(plugin_data->sv_last_note < 0.0f)
            {
                plugin_data->data[f_voice]->last_pitch =
                        (plugin_data->data[f_voice]->note_f);
            }
            else
            {
                plugin_data->data[f_voice]->last_pitch =
                        (plugin_data->sv_last_note);
            }

            plugin_data->data[f_voice]->osc1_pitch_adjust =
                    (*plugin_data->osc1pitch) +
                    ((*plugin_data->osc1tune) * 0.01f);
            plugin_data->data[f_voice]->osc2_pitch_adjust =
                    (*plugin_data->osc2pitch) +
                    ((*plugin_data->osc2tune) * 0.01f);

            v_rmp_retrigger_glide_t(&plugin_data->data[f_voice]->glide_env,
                    (*(plugin_data->master_glide) * 0.01f),
                    (plugin_data->data[f_voice]->last_pitch),
                    (plugin_data->data[f_voice]->target_pitch));

            plugin_data->data[f_voice]->osc1_linamp =
                    f_db_to_linear_fast(*(plugin_data->osc1vol));
            plugin_data->data[f_voice]->osc2_linamp =
                    f_db_to_linear_fast(*(plugin_data->osc2vol));
            plugin_data->data[f_voice]->noise_linamp =
                    f_db_to_linear_fast(*(plugin_data->noise_amp));

            plugin_data->data[f_voice]->unison_spread =
                    (*plugin_data->master_uni_spread) * 0.01f;

            v_adsr_retrigger(&plugin_data->data[f_voice]->adsr_amp);
            v_adsr_retrigger(&plugin_data->data[f_voice]->adsr_filter);

            v_lfs_sync(&plugin_data->data[f_voice]->lfo1,
                    *plugin_data->lfo_phase * 0.01f,
                    *plugin_data->lfo_type);

            float f_attack = *(plugin_data->attack) * .01;
            f_attack = (f_attack) * (f_attack);
            float f_decay = *(plugin_data->decay) * .01;
            f_decay = (f_decay) * (f_decay);
            float f_release = *(plugin_data->release) * .01;
            f_release = (f_release) * (f_release);

            FP_ADSR_SET[f_adsr_main_lin](&plugin_data->data[f_voice]->adsr_amp,
                    (f_attack), (f_decay), *(plugin_data->sustain),
                    (f_release));

            float f_attack_f = *(plugin_data->attack_f) * .01;
            f_attack_f = (f_attack_f) * (f_attack_f);
            float f_decay_f = *(plugin_data->decay_f) * .01;
            f_decay_f = (f_decay_f) * (f_decay_f);
            float f_release_f = *(plugin_data->release_f) * .01;
            f_release_f = (f_release_f) * (f_release_f);

            v_adsr_set_adsr(&plugin_data->data[f_voice]->adsr_filter,
                    (f_attack_f), (f_decay_f),
                    *(plugin_data->sustain_f) * 0.01f, (f_release_f));

            v_rmp_retrigger_curve(&plugin_data->data[f_voice]->pitch_env,
                    *(plugin_data->pitch_env_time) * 0.01f,
                    *(plugin_data->pitch_env_amt),
                    *(plugin_data->ramp_curve) * 0.01f);

            v_clp_set_in_gain(&plugin_data->data[f_voice]->clipper1,
                    *plugin_data->dist);

            v_svf_set_res(&plugin_data->data[f_voice]->svf_filter,
                    (*plugin_data->res) * 0.1f);

            plugin_data->data[f_voice]->noise_amp =
                    f_db_to_linear(*(plugin_data->noise_amp));

            v_axf_set_xfade(&plugin_data->data[f_voice]->dist_dry_wet,
                    *(plugin_data->dist_wet) * 0.01f);

            plugin_data->data[f_voice]->hard_sync =
                    (int)(*plugin_data->sync_hard);

            v_osc_set_simple_osc_unison_type(
                    &plugin_data->data[f_voice]->osc_unison1,
                    (int)(*plugin_data->osc1type));
            v_osc_set_simple_osc_unison_type(
                    &plugin_data->data[f_voice]->osc_unison2,
                    (int)(*plugin_data->osc2type));

            v_svf_reset(&plugin_data->data[f_voice]->svf_filter);

            if(f_poly_mode == 0)
            {
                v_osc_note_on_sync_phases(
                        &plugin_data->data[f_voice]->osc_unison1);
                v_osc_note_on_sync_phases(
                        &plugin_data->data[f_voice]->osc_unison2);
            }

            v_osc_set_uni_voice_count(
                    &plugin_data->data[f_voice]->osc_unison1,
                    *plugin_data->master_uni_voice);

            if(plugin_data->data[f_voice]->hard_sync)
            {
                v_osc_set_uni_voice_count(
                    &plugin_data->data[f_voice]->osc_unison2, 1);
            }
            else
            {
                v_osc_set_uni_voice_count(
                    &plugin_data->data[f_voice]->osc_unison2,
                    *plugin_data->master_uni_voice);
            }

            plugin_data->data[f_voice]->adsr_prefx =
                    (int)*plugin_data->adsr_prefx;

            plugin_data->sv_last_note =
                    (plugin_data->data[f_voice]->note_f);
        }
        /*0 velocity, the same as note-off*/
        else
        {
            v_voc_note_off(plugin_data->voices,
                    a_event->note,
                    (plugin_data->sampleNo),
                    (a_event->tick));
        }
    }
    else if (a_event->type == PYDAW_EVENT_NOTEOFF)
    {
        v_voc_note_off(plugin_data->voices,
                a_event->note,
                (plugin_data->sampleNo),
                (a_event->tick));
    }
    else if (a_event->type == PYDAW_EVENT_CONTROLLER)
    {
        assert(a_event->param >= 1 && a_event->param < 128);

        v_plugin_event_queue_add(&plugin_data->midi_queue,
            PYDAW_EVENT_CONTROLLER, a_event->tick,
            a_event->value, a_event->param);

    }
    else if (a_event->type == PYDAW_EVENT_PITCHBEND)
    {
        v_plugin_event_queue_add(&plugin_data->midi_queue,
            PYDAW_EVENT_PITCHBEND, a_event->tick,
            a_event->value * 0.00012207f, 0);
    }
}

static void v_run_rayv(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_rayv *plugin_data = (t_rayv *) instance;

    t_pydaw_seq_event **events = (t_pydaw_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    int f_poly_mode = (int)(*plugin_data->mono_mode);

    int midi_event_pos = 0;

    if(f_poly_mode == 2 && plugin_data->voices->poly_mode != 2)
    {
        rayvPanic(instance);  //avoid hung notes
    }

    plugin_data->voices->poly_mode = f_poly_mode;

    register int f_i;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_rayv_process_midi_event(plugin_data, events[f_i], f_poly_mode);
    }

    f_i = 0;

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_pydaw_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i)
    {
        ev_tmp = (t_pydaw_seq_event*)atm_events->data[f_i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue, ev_tmp->type,
            ev_tmp->tick, ev_tmp->value, ev_tmp->port);
    }

    plugin_data->master_vol_lin = f_db_to_linear_fast(*plugin_data->master_vol);

    int f_i2;
    t_plugin_event_queue_item * f_midi_item;

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        while(1)
        {
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue, f_i);
            if(!f_midi_item)
            {
                break;
            }

            if(f_midi_item->type == PYDAW_EVENT_PITCHBEND)
            {
                plugin_data->sv_pitch_bend_value = f_midi_item->value;
            }
            else if(f_midi_item->type == PYDAW_EVENT_CONTROLLER)
            {
                v_cc_map_translate(
                    &plugin_data->cc_map, plugin_data->descriptor,
                    plugin_data->port_table,
                    f_midi_item->port, f_midi_item->value);
            }

            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue, f_i, plugin_data->port_table);

        v_sml_run(&plugin_data->mono_modules->lfo_smoother,
                (*plugin_data->lfo_freq));
        v_sml_run(&plugin_data->mono_modules->filter_smoother,
                (*plugin_data->timbre));
        v_sml_run(&plugin_data->mono_modules->pitchbend_smoother,
                (plugin_data->sv_pitch_bend_value));

        for(f_i2 = 0; f_i2 < RAYV_POLYPHONY; ++f_i2)
        {
            if((plugin_data->data[f_i2]->adsr_amp.stage) != ADSR_STAGE_OFF)
            {
                v_run_rayv_voice(plugin_data,
                    &plugin_data->voices->voices[f_i2],
                    plugin_data->data[f_i2],
                    plugin_data->output0, plugin_data->output1, f_i);
            }
            else
            {
                plugin_data->voices->voices[f_i2].n_state = note_state_off;
            }
        }

        ++plugin_data->sampleNo;
    }
}

static void v_run_rayv_voice(t_rayv *plugin_data,
        t_voc_single_voice * a_poly_voice, t_rayv_poly_voice *a_voice,
        PYFX_Data *out0, PYFX_Data *out1, int a_i)
{
    if((plugin_data->sampleNo) < (a_poly_voice->on))
    {
        return;
    }

    if ((plugin_data->sampleNo == a_poly_voice->off) &&
       ((a_voice->adsr_amp.stage) < ADSR_STAGE_RELEASE))
    {
        if(a_poly_voice->n_state == note_state_killed)
        {
            v_rayv_poly_note_off(a_voice, 1);
        }
        else
        {
            v_rayv_poly_note_off(a_voice, 0);
        }
    }

    a_voice->current_sample = 0.0f;

    f_rmp_run_ramp_curve(&a_voice->pitch_env);
    f_rmp_run_ramp(&a_voice->glide_env);

    v_lfs_set(&a_voice->lfo1,
            (plugin_data->mono_modules->lfo_smoother.last_value) * 0.01f);
    v_lfs_run(&a_voice->lfo1);
    a_voice->lfo_amp_output =
        f_db_to_linear_fast((((*plugin_data->lfo_amp) *
        (a_voice->lfo1.output)) - (f_lms_abs((*plugin_data->lfo_amp)) * 0.5)));
    a_voice->lfo_filter_output =
            (*plugin_data->lfo_filter) * (a_voice->lfo1.output);
    a_voice->lfo_pitch_output =
            (*plugin_data->lfo_pitch + (*plugin_data->lfo_pitch_fine * 0.01f))
            * (a_voice->lfo1.output);

    if(a_voice->hard_sync)
    {
        a_voice->base_pitch =
                (a_voice->glide_env.output_multiplied) +
                (a_voice->pitch_env.output_multiplied)
                + (plugin_data->mono_modules->pitchbend_smoother.last_value *
                (*(plugin_data->master_pb_amt))) +
                (a_voice->last_pitch) + (a_voice->lfo_pitch_output);

        v_osc_set_unison_pitch(&a_voice->osc_unison1, a_voice->unison_spread,
                ((a_voice->target_pitch) + (a_voice->osc1_pitch_adjust) ));
        v_osc_set_unison_pitch(&a_voice->osc_unison2, a_voice->unison_spread,
                ((a_voice->base_pitch) + (a_voice->osc2_pitch_adjust)));

        a_voice->current_sample +=
                f_osc_run_unison_osc_sync(&a_voice->osc_unison2);

        if(a_voice->osc_unison2.is_resetting)
        {
            v_osc_note_on_sync_phases_hard(&a_voice->osc_unison1);
        }

        a_voice->current_sample +=
                f_osc_run_unison_osc(&a_voice->osc_unison1) *
                (a_voice->osc1_linamp);

    }
    else
    {
        a_voice->base_pitch =
                (a_voice->glide_env.output_multiplied) +
                (a_voice->pitch_env.output_multiplied)
                + (plugin_data->mono_modules->pitchbend_smoother.last_value *
                (*(plugin_data->master_pb_amt))) +
                (a_voice->last_pitch) + (a_voice->lfo_pitch_output);

        v_osc_set_unison_pitch(&a_voice->osc_unison1,
                (*plugin_data->master_uni_spread) * 0.01f,
                ((a_voice->base_pitch) + (a_voice->osc1_pitch_adjust) ));
        v_osc_set_unison_pitch(&a_voice->osc_unison2,
                (*plugin_data->master_uni_spread) * 0.01f,
                ((a_voice->base_pitch) + (a_voice->osc2_pitch_adjust)));

        a_voice->current_sample +=
            f_osc_run_unison_osc(&a_voice->osc_unison1) * (a_voice->osc1_linamp);
        a_voice->current_sample +=
            f_osc_run_unison_osc(&a_voice->osc_unison2) * (a_voice->osc2_linamp);
    }

    a_voice->current_sample +=
        (f_run_white_noise(&a_voice->white_noise1) * (a_voice->noise_linamp));

    a_voice->adsr_run_func(&a_voice->adsr_amp);

    if(a_voice->adsr_prefx)
    {
        a_voice->current_sample *= (a_voice->adsr_amp.output);
    }

    v_adsr_run(&a_voice->adsr_filter);

    v_svf_set_cutoff_base(&a_voice->svf_filter,
            (plugin_data->mono_modules->filter_smoother.last_value));

    v_svf_add_cutoff_mod(&a_voice->svf_filter,
            (((a_voice->adsr_filter.output) * (*plugin_data->filter_env_amt)) +
            (a_voice->lfo_filter_output) +
            (a_voice->filter_keytrk)));

    v_svf_set_cutoff(&a_voice->svf_filter);

    a_voice->filter_output = a_voice->svf_function(&a_voice->svf_filter,
            (a_voice->current_sample));

    a_voice->current_sample = f_axf_run_xfade(&a_voice->dist_dry_wet,
            (a_voice->filter_output),
            f_clp_clip(&a_voice->clipper1, (a_voice->filter_output)));

    a_voice->current_sample = (a_voice->current_sample) *
        (a_voice->amp) * (a_voice->lfo_amp_output) *
        plugin_data->master_vol_lin;

    if(!a_voice->adsr_prefx)
    {
        a_voice->current_sample *= (a_voice->adsr_amp.output);
    }

    /*Run the envelope and assign to the output buffers*/
    out0[a_i] += (a_voice->current_sample);
    out1[a_i] += (a_voice->current_sample);
}

PYFX_Descriptor *rayv_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = pydaw_get_pyfx_descriptor(RAYV_COUNT);

    pydaw_set_pyfx_port(f_result, RAYV_ATTACK, 10.0f, 0.0f, 200.0f);
    pydaw_set_pyfx_port(f_result, RAYV_DECAY, 10.0f, 10.0f, 200.0f);
    pydaw_set_pyfx_port(f_result, RAYV_SUSTAIN, 0.0f, -60.0f, 0.0f);
    pydaw_set_pyfx_port(f_result, RAYV_RELEASE, 50.0f, 10.0f, 400.0f);
    pydaw_set_pyfx_port(f_result, RAYV_TIMBRE, 124.0f, 20.0f, 124.0f);
    pydaw_set_pyfx_port(f_result, RAYV_RES, -120.0f, -300.0f, 0.0f);
    pydaw_set_pyfx_port(f_result, RAYV_DIST, 15.0f, 0.0f, 48.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_ATTACK, 10.0f, 0.0f, 200.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_DECAY, 50.0f, 10.0f, 200.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_SUSTAIN, 100.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_RELEASE, 50.0f, 10.0f, 400.0f);
    pydaw_set_pyfx_port(f_result, RAYV_NOISE_AMP, -30.0f, -60.0f, 0.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_ENV_AMT, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_DIST_WET, 0.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC1_TYPE, 1.0f, 0.0f, 5.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC1_PITCH, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC1_TUNE, 0.0f, -100.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC1_VOLUME, -6.0f, -30.0f, 0.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC2_TYPE, 0.0f, 0.0f, 5.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC2_PITCH, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC2_TUNE, 0.0f, -100.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC2_VOLUME, -6.0f, -30.0f, 0.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_VOLUME, -6.0f, -30.0f, 12.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_UNISON_VOICES, 1.0f, 1.0f, 7.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_UNISON_SPREAD, 50.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_GLIDE, 0.0f,  0.0f, 200.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_PITCHBEND_AMT, 18.0f, 1.0f,  36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_PITCH_ENV_AMT, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_PITCH_ENV_TIME, 100.0f, 1.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_FREQ, 200.0f, 10.0f, 1600.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_TYPE, 0.0f, 0.0f, 2.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_AMP, 0.0f, -24.0f, 24.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_PITCH, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_FILTER, 0.0f, -48.0f, 48.0f);
    pydaw_set_pyfx_port(f_result, RAYV_OSC_HARD_SYNC, 0.0f, 0.0f, 1.0f);
    pydaw_set_pyfx_port(f_result, RAYV_RAMP_CURVE, 50.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_FILTER_KEYTRK, 0.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MONO_MODE, 0.0f, 0.0f, 3.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_PHASE, 0.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_LFO_PITCH_FINE, 0.0f, -100.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, RAYV_ADSR_PREFX, 0.0f, 0.0f, 1.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MIN_NOTE, 0.0f, 0.0f, 120.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MAX_NOTE, 120.0f, 0.0f, 120.0f);
    pydaw_set_pyfx_port(f_result, RAYV_MASTER_PITCH, 0.0f, -36.0f, 36.0f);
    pydaw_set_pyfx_port(f_result, RAYV_ADSR_LIN_MAIN, 1.0f, 0.0f, 1.0f);

    f_result->cleanup = v_cleanup_rayv;
    f_result->connect_port = v_rayv_connect_port;
    f_result->connect_buffer = v_rayv_connect_buffer;
    f_result->instantiate = g_rayv_instantiate;
    f_result->panic = rayvPanic;
    f_result->load = v_rayv_load;
    f_result->set_port_value = v_rayv_set_port_value;
    f_result->set_cc_map = v_rayv_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_run_rayv;
    f_result->offline_render_prep = v_rayv_or_prep;
    f_result->on_stop = v_rayv_on_stop;

    return f_result;
}
