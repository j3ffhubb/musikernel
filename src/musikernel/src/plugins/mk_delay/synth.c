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
#include "../../libmodsynth/modules/filter/svf.h"
#include "synth.h"

static void v_mkdelay_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_mkdelay_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_mkdelay *plugin = (t_mkdelay *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_mkdelay_panic(PYFX_Handle instance)
{
    t_mkdelay *plugin = (t_mkdelay*)instance;

    register int f_i = 0;
    while(f_i < plugin->mono_modules->delay->delay0.sample_count)
    {
        plugin->mono_modules->delay->delay0.buffer[f_i] = 0.0f;
        plugin->mono_modules->delay->delay1.buffer[f_i] = 0.0f;
        ++f_i;
    }
}

static void v_mkdelay_on_stop(PYFX_Handle instance)
{
    //t_mkdelay *plugin = (t_mkdelay*)instance;
}

static void v_mkdelay_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }

    t_mkdelay *plugin = (t_mkdelay*)instance;

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

static void v_mkdelay_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_mkdelay *plugin;

    plugin = (t_mkdelay *) instance;

    switch (port)
    {
        case MKDELAY_DELAY_TIME: plugin->delay_time = data; break;
        case MKDELAY_FEEDBACK: plugin->feedback = data; break;
        case MKDELAY_DRY: plugin->dry = data;  break;
        case MKDELAY_WET: plugin->wet = data; break;
        case MKDELAY_DUCK: plugin->duck = data; break;
        case MKDELAY_CUTOFF: plugin->cutoff = data; break;
        case MKDELAY_STEREO: plugin->stereo = data; break;
    }
}

static PYFX_Handle g_mkdelay_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_mkdelay *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_mkdelay));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;


    plugin_data->mono_modules =
            v_mkdelay_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_mkdelay_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_mkdelay *plugin_data = (t_mkdelay*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_mkdelay_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_mkdelay *plugin_data = (t_mkdelay*)Instance;
    plugin_data->port_table[a_port] = a_value;
}


static void v_mkdelay_process_midi_event(
    t_mkdelay * plugin_data, t_seq_event * a_event)
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

static void v_mkdelay_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mkdelay *plugin_data = (t_mkdelay*)instance;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    register int f_i;

    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_mkdelay_process_midi_event(plugin_data, events[f_i]);
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
            &plugin_data->atm_queue, f_i,
            plugin_data->port_table);

        v_sml_run(plugin_data->mono_modules->time_smoother,
            (*(plugin_data->delay_time)));

        v_ldl_set_delay(plugin_data->mono_modules->delay,
            (plugin_data->mono_modules->time_smoother->last_value * 0.01f),
            (*plugin_data->feedback) * 0.1f,
            (*plugin_data->wet) * 0.1f, (*plugin_data->dry) * 0.1f,
            (*(plugin_data->stereo) * .01), (*plugin_data->duck),
            (*plugin_data->cutoff));

        v_ldl_run_delay(plugin_data->mono_modules->delay,
                (plugin_data->output0[(f_i)]),
                (plugin_data->output1[(f_i)]));

        plugin_data->output0[(f_i)] =
                (plugin_data->mono_modules->delay->output0);
        plugin_data->output1[(f_i)] =
                (plugin_data->mono_modules->delay->output1);

        ++f_i;
    }
}

PYFX_Descriptor *mkdelay_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = get_pyfx_descriptor(MKDELAY_COUNT);

    set_pyfx_port(f_result, MKDELAY_DELAY_TIME, 50.0f, 10.0f, 100.0f);
    set_pyfx_port(f_result, MKDELAY_FEEDBACK, -120.0f, -200.0f, 0.0f);
    set_pyfx_port(f_result, MKDELAY_DRY, 0.0f, -300.0f, 0.0f);
    set_pyfx_port(f_result, MKDELAY_WET, -120.0f, -300.0f, 0.0f);
    set_pyfx_port(f_result, MKDELAY_DUCK, -20.0f, -40.0f, 0.0f);
    set_pyfx_port(f_result, MKDELAY_CUTOFF, 90.0f, 40.0f, 118.0f);
    set_pyfx_port(f_result, MKDELAY_STEREO, 100.0f, 0.0f, 100.0f);


    f_result->cleanup = v_mkdelay_cleanup;
    f_result->connect_port = v_mkdelay_connect_port;
    f_result->connect_buffer = v_mkdelay_connect_buffer;
    f_result->instantiate = g_mkdelay_instantiate;
    f_result->panic = v_mkdelay_panic;
    f_result->load = v_mkdelay_load;
    f_result->set_port_value = v_mkdelay_set_port_value;
    f_result->set_cc_map = v_mkdelay_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_mkdelay_run;
    f_result->on_stop = v_mkdelay_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}




/*
void v_mkdelay_destructor()
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
