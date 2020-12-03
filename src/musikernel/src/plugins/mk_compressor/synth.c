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


static void v_mk_comp_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_mk_comp_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_mk_comp *plugin = (t_mk_comp *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_mk_comp_panic(PYFX_Handle instance)
{
    //t_mk_comp *plugin = (t_mk_comp*)instance;
}

static void v_mk_comp_on_stop(PYFX_Handle instance)
{
    //t_mk_comp *plugin = (t_mk_comp*)instance;
}

static void v_mk_comp_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    t_mk_comp *plugin = (t_mk_comp*)instance;

    if(!a_is_sidechain)
    {
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
}

static void v_mk_comp_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_mk_comp *plugin;

    plugin = (t_mk_comp *) instance;

    switch (port)
    {
        case MK_COMP_THRESHOLD: plugin->threshold = data; break;
        case MK_COMP_RATIO: plugin->ratio = data; break;
        case MK_COMP_KNEE: plugin->knee = data; break;
        case MK_COMP_ATTACK: plugin->attack = data; break;
        case MK_COMP_RELEASE: plugin->release = data; break;
        case MK_COMP_GAIN: plugin->gain = data; break;
        case MK_COMP_MODE: plugin->mode = data; break;
        case MK_COMP_RMS_TIME: plugin->rms_time = data; break;
        case MK_COMP_UI_MSG_ENABLED: plugin->peak_meter = data; break;
    }
}

static PYFX_Handle g_mk_comp_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_mk_comp *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_mk_comp));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules = v_mk_comp_mono_init(s_rate, a_plugin_uid);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_mk_comp_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_mk_comp *plugin_data = (t_mk_comp*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_mk_comp_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_mk_comp *plugin_data = (t_mk_comp*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static void v_mk_comp_process_midi_event(
    t_mk_comp * plugin_data, t_seq_event * a_event)
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

static void v_mk_comp_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mk_comp *plugin_data = (t_mk_comp*)instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int f_i = 0;
    int midi_event_pos = 0;
    int f_is_rms = (int)(*plugin_data->mode);
    t_cmp_compressor * f_cmp = &plugin_data->mono_modules->compressor;
    MKFLT f_gain = f_db_to_linear_fast((*plugin_data->gain) * 0.1f);
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_mk_comp_process_midi_event(plugin_data, events[f_i]);
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

    f_i = 0;

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

        v_cmp_set(f_cmp,
            *plugin_data->threshold * 0.1f, (*plugin_data->ratio) * 0.1f,
            *plugin_data->knee * 0.1f, *plugin_data->attack * 0.001f,
            *plugin_data->release * 0.001f, *plugin_data->gain * 0.1f);

        if(f_is_rms)
        {
            v_cmp_set_rms(f_cmp, (*plugin_data->rms_time) * 0.01f);
            v_cmp_run_rms(
                f_cmp, plugin_data->output0[f_i], plugin_data->output1[f_i]);
        }
        else
        {
            v_cmp_run(
                f_cmp, plugin_data->output0[f_i], plugin_data->output1[f_i]);
        }

        plugin_data->output0[f_i] = f_cmp->output0 * f_gain;
        plugin_data->output1[f_i] = f_cmp->output1 * f_gain;
        ++f_i;
    }

    if((int)(*plugin_data->peak_meter))
    {
        if(f_cmp->peak_tracker.dirty)
        {
            sprintf(plugin_data->ui_msg_buff, "%i|gain|%f",
                plugin_data->plugin_uid, f_cmp->peak_tracker.gain_redux);
            plugin_data->queue_func("ui", plugin_data->ui_msg_buff);
            v_pkm_redux_lin_reset(&f_cmp->peak_tracker);
        }
    }
}


PYFX_Descriptor *mk_comp_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = get_pyfx_descriptor(MK_COMP_COUNT);

    set_pyfx_port(f_result, MK_COMP_THRESHOLD, -240.0f, -360.0f, -60.0f);
    set_pyfx_port(f_result, MK_COMP_RATIO, 20.0f, 10.0f, 100.0f);
    set_pyfx_port(f_result, MK_COMP_KNEE, 0.0f, 0.0f, 120.0f);
    set_pyfx_port(f_result, MK_COMP_ATTACK, 50.0f, 0.0f, 500.0f);
    set_pyfx_port(f_result, MK_COMP_RELEASE, 100.0f, 10.0f, 500.0f);
    set_pyfx_port(f_result, MK_COMP_GAIN, 0.0f, -360.0f, 360.0f);
    set_pyfx_port(f_result, MK_COMP_MODE, 0.0f, 0.0f, 1.0f);
    set_pyfx_port(f_result, MK_COMP_RMS_TIME, 2.0f, 1.0f, 5.0f);
    set_pyfx_port(f_result, MK_COMP_UI_MSG_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_mk_comp_cleanup;
    f_result->connect_port = v_mk_comp_connect_port;
    f_result->connect_buffer = v_mk_comp_connect_buffer;
    f_result->instantiate = g_mk_comp_instantiate;
    f_result->panic = v_mk_comp_panic;
    f_result->load = v_mk_comp_load;
    f_result->set_port_value = v_mk_comp_set_port_value;
    f_result->set_cc_map = v_mk_comp_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_mk_comp_run;
    f_result->on_stop = v_mk_comp_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}




/*
void v_mk_comp_destructor()
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
