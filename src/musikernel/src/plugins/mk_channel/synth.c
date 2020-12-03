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

#include "../../plugin.h"
#include "libmodsynth.h"
#include "../../libmodsynth/lib/amp.h"
#include "synth.h"


static void v_mkchnl_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_mkchnl_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_mkchnl *plugin = (t_mkchnl *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_mkchnl_panic(PYFX_Handle instance)
{
    //t_mkchnl *plugin = (t_mkchnl*)instance;
}

static void v_mkchnl_on_stop(PYFX_Handle instance)
{
    //t_mkchnl *plugin = (t_mkchnl*)instance;
}

static void v_mkchnl_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }

    t_mkchnl *plugin = (t_mkchnl*)instance;
    plugin->buffers[a_index] = DataLocation;
}

static void v_mkchnl_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_mkchnl *plugin;

    plugin = (t_mkchnl *) instance;

    switch (port)
    {
        case MKCHNL_VOL_SLIDER: plugin->vol_slider = data; break;
        case MKCHNL_GAIN: plugin->gain = data; break;
        case MKCHNL_PAN: plugin->pan = data; break;
        case MKCHNL_LAW: plugin->pan_law = data; break;
    }
}

static PYFX_Handle g_mkchnl_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_mkchnl *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_mkchnl));
    hpalloc((void**)&plugin_data->buffers, sizeof(MKFLT*) * 2);

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules =
            v_mkchnl_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_mkchnl_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_mkchnl *plugin_data = (t_mkchnl*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_mkchnl_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_mkchnl *plugin_data = (t_mkchnl*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static void v_mkchnl_process_midi_event(
    t_mkchnl * plugin_data, t_seq_event * a_event)
{

    if (a_event->type == PYDAW_EVENT_CONTROLLER)
    {
        assert(a_event->param >= 1 && a_event->param < 128);

        plugin_data->midi_event_types[plugin_data->midi_event_count] =
                PYDAW_EVENT_CONTROLLER;
        plugin_data->midi_event_ticks[plugin_data->midi_event_count] =
                a_event->tick;
        plugin_data->midi_event_ports[plugin_data->midi_event_count] =
                a_event->param;
        plugin_data->midi_event_values[plugin_data->midi_event_count] =
                a_event->value;

        ++plugin_data->midi_event_count;
    }
}


static void v_mkchnl_process_midi(
        PYFX_Handle instance, struct ShdsList * events,
        struct ShdsList * atm_events)
{
    t_mkchnl *plugin_data = (t_mkchnl*)instance;
    register int f_i = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < events->len; ++f_i)
    {
        v_mkchnl_process_midi_event(
            plugin_data, (t_seq_event*)events->data[f_i]);
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i)
    {
        ev_tmp = (t_seq_event*)atm_events->data[f_i];
        v_plugin_event_queue_add(
            &plugin_data->atm_queue, ev_tmp->type,
            ev_tmp->tick, ev_tmp->value, ev_tmp->port);
    }
}


static void v_mkchnl_run_mixing(
        PYFX_Handle instance, int sample_count,
        MKFLT ** output_buffers, int output_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mkchnl *plugin_data = (t_mkchnl*)instance;

    v_mkchnl_process_midi(instance, midi_events, atm_events);

    MKFLT f_vol_linear;
    MKFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.01f);
    MKFLT f_pan_law = (*plugin_data->pan_law) * 0.01f;

    int midi_event_pos = 0;
    register int f_i = 0;

    while(f_i < sample_count)
    {
        while(midi_event_pos < plugin_data->midi_event_count &&
            plugin_data->midi_event_ticks[midi_event_pos] == f_i)
        {
            if(plugin_data->midi_event_types[midi_event_pos] ==
                    PYDAW_EVENT_CONTROLLER)
            {
                v_cc_map_translate(
                    &plugin_data->cc_map, plugin_data->descriptor,
                    plugin_data->port_table,
                    plugin_data->midi_event_ports[midi_event_pos],
                    plugin_data->midi_event_values[midi_event_pos]);
            }
            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue, f_i, plugin_data->port_table);

        v_sml_run(&plugin_data->mono_modules->volume_smoother,
            (*plugin_data->vol_slider * 0.01f));

        v_sml_run(&plugin_data->mono_modules->pan_smoother,
            (*plugin_data->pan * 0.01f));

        v_pn2_set(&plugin_data->mono_modules->panner,
            plugin_data->mono_modules->pan_smoother.last_value, f_pan_law);

        f_vol_linear = f_db_to_linear_fast(
            (plugin_data->mono_modules->volume_smoother.last_value));

        output_buffers[0][f_i] += plugin_data->buffers[0][f_i] *
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainL;
        output_buffers[1][f_i] += plugin_data->buffers[1][f_i] *
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainR;

        ++f_i;
    }

}

static void v_mkchnl_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mkchnl *plugin_data = (t_mkchnl*)instance;

    v_mkchnl_process_midi(instance, midi_events, atm_events);

    int midi_event_pos = 0;
    int f_i = 0;

    MKFLT f_vol_linear;

    MKFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.01f);
    MKFLT f_pan_law = (*plugin_data->pan_law) * 0.01f;

    while(f_i < sample_count)
    {
        while(midi_event_pos < plugin_data->midi_event_count &&
            plugin_data->midi_event_ticks[midi_event_pos] == f_i)
        {
            if(plugin_data->midi_event_types[midi_event_pos] ==
                    PYDAW_EVENT_CONTROLLER)
            {
                v_cc_map_translate(
                    &plugin_data->cc_map, plugin_data->descriptor,
                    plugin_data->port_table,
                    plugin_data->midi_event_ports[midi_event_pos],
                    plugin_data->midi_event_values[midi_event_pos]);
            }
            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue, f_i, plugin_data->port_table);

        v_sml_run(&plugin_data->mono_modules->volume_smoother,
            (*plugin_data->vol_slider * 0.01f));

        v_sml_run(&plugin_data->mono_modules->pan_smoother,
            (*plugin_data->pan * 0.01f));

        v_pn2_set(&plugin_data->mono_modules->panner,
            plugin_data->mono_modules->pan_smoother.last_value, f_pan_law);

        f_vol_linear = f_db_to_linear_fast(
            (plugin_data->mono_modules->volume_smoother.last_value));

        plugin_data->buffers[0][f_i] *=
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainL;
        plugin_data->buffers[1][f_i] *=
            f_vol_linear * f_gain * plugin_data->mono_modules->panner.gainR;

        ++f_i;
    }
}

PYFX_Descriptor *mkchnl_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = get_pyfx_descriptor(MKCHNL_COUNT);

    set_pyfx_port(f_result, MKCHNL_VOL_SLIDER, 0.0f, -5000.0f, 0.0f);
    set_pyfx_port(f_result, MKCHNL_GAIN, 0.0f, -2400.0f, 2400.0f);
    set_pyfx_port(f_result, MKCHNL_PAN, 0.0f, -100.0f, 100.0f);
    set_pyfx_port(f_result, MKCHNL_LAW, -300.0f, -600.0f, 0.0f);

    f_result->cleanup = v_mkchnl_cleanup;
    f_result->connect_port = v_mkchnl_connect_port;
    f_result->connect_buffer = v_mkchnl_connect_buffer;
    f_result->instantiate = g_mkchnl_instantiate;
    f_result->panic = v_mkchnl_panic;
    f_result->load = v_mkchnl_load;
    f_result->set_port_value = v_mkchnl_set_port_value;
    f_result->set_cc_map = v_mkchnl_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_mkchnl_run;
    f_result->run_mixing = v_mkchnl_run_mixing;
    f_result->on_stop = v_mkchnl_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}


/*
void v_mkchnl_destructor()
{
    if (f_result) {
	free((PYFX_PortDescriptor *) f_result->PortDescriptors);
	free((char **) f_result->PortNames);
	free((PYFX_PortRangeHint *) f_result->PortRangeHints);
	free(f_result);
    }
    if (LMSDDescriptor) {
	free(LMSDDescriptor);
    }
}
*/
