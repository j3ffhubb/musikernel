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
#include "synth.h"


static void v_mkeq_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_mkeq_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_mkeq *plugin = (t_mkeq *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_mkeq_panic(PYFX_Handle instance)
{
    //t_mkeq *plugin = (t_mkeq*)instance;
}

static void v_mkeq_on_stop(PYFX_Handle instance)
{
    //t_mkeq *plugin = (t_mkeq*)instance;
}

static void v_mkeq_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }

    t_mkeq *plugin = (t_mkeq*)instance;

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

static void v_mkeq_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_mkeq *plugin;

    plugin = (t_mkeq *) instance;

    switch (port)
    {
        case MKEQ_EQ1_FREQ: plugin->eq_freq[0] = data; break;
        case MKEQ_EQ2_FREQ: plugin->eq_freq[1] = data; break;
        case MKEQ_EQ3_FREQ: plugin->eq_freq[2] = data; break;
        case MKEQ_EQ4_FREQ: plugin->eq_freq[3] = data; break;
        case MKEQ_EQ5_FREQ: plugin->eq_freq[4] = data; break;
        case MKEQ_EQ6_FREQ: plugin->eq_freq[5] = data; break;

        case MKEQ_EQ1_RES: plugin->eq_res[0] = data; break;
        case MKEQ_EQ2_RES: plugin->eq_res[1] = data; break;
        case MKEQ_EQ3_RES: plugin->eq_res[2] = data; break;
        case MKEQ_EQ4_RES: plugin->eq_res[3] = data; break;
        case MKEQ_EQ5_RES: plugin->eq_res[4] = data; break;
        case MKEQ_EQ6_RES: plugin->eq_res[5] = data; break;

        case MKEQ_EQ1_GAIN: plugin->eq_gain[0] = data; break;
        case MKEQ_EQ2_GAIN: plugin->eq_gain[1] = data; break;
        case MKEQ_EQ3_GAIN: plugin->eq_gain[2] = data; break;
        case MKEQ_EQ4_GAIN: plugin->eq_gain[3] = data; break;
        case MKEQ_EQ5_GAIN: plugin->eq_gain[4] = data; break;
        case MKEQ_EQ6_GAIN: plugin->eq_gain[5] = data; break;
        case MKEQ_SPECTRUM_ENABLED: plugin->spectrum_analyzer_on = data; break;
    }
}

static PYFX_Handle g_mkeq_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_mkeq *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_mkeq));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules =
            v_mkeq_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_pydaw_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_mkeq_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_mkeq *plugin_data = (t_mkeq*)instance;
    pydaw_generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_mkeq_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_mkeq *plugin_data = (t_mkeq*)Instance;
    plugin_data->port_table[a_port] = a_value;
}


static void v_mkeq_process_midi_event(
    t_mkeq * plugin_data, t_pydaw_seq_event * a_event)
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

static void v_mkeq_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mkeq *plugin_data = (t_mkeq*)instance;

    t_pydaw_seq_event **events = (t_pydaw_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    register int f_i = 0;
    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_mkeq_process_midi_event(plugin_data, events[f_i]);
    }

    v_plugin_event_queue_reset(&plugin_data->atm_queue);

    t_pydaw_seq_event * ev_tmp;
    for(f_i = 0; f_i < atm_events->len; ++f_i)
    {
        ev_tmp = (t_pydaw_seq_event*)atm_events->data[f_i];
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

        int f_i2 = 0;

        while(f_i2 < MKEQ_EQ_COUNT)
        {
            if(*plugin_data->eq_gain[f_i2] != 0.0f)
            {
                v_pkq_calc_coeffs(&plugin_data->mono_modules->eqs[f_i2],
                        *plugin_data->eq_freq[f_i2],
                        *plugin_data->eq_res[f_i2] * 0.01f,
                        *plugin_data->eq_gain[f_i2] * 0.1f);
                v_pkq_run(&plugin_data->mono_modules->eqs[f_i2],
                        plugin_data->output0[f_i],
                        plugin_data->output1[f_i]);
                plugin_data->output0[f_i] =
                        plugin_data->mono_modules->eqs[f_i2].output0;
                plugin_data->output1[f_i] =
                        plugin_data->mono_modules->eqs[f_i2].output1;
            }
            ++f_i2;
        }

        ++f_i;
    }

    if((int)(*plugin_data->spectrum_analyzer_on))
    {
        v_spa_run(plugin_data->mono_modules->spectrum_analyzer,
                plugin_data->output0, plugin_data->output1, sample_count);
        if(plugin_data->mono_modules->spectrum_analyzer->str_buf[0] != '\0')
        {
            plugin_data->queue_func("ui",
                plugin_data->mono_modules->spectrum_analyzer->str_buf);
            plugin_data->mono_modules->spectrum_analyzer->str_buf[0] = '\0';
        }
    }

}

PYFX_Descriptor *mkeq_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = pydaw_get_pyfx_descriptor(MKEQ_COUNT);


    pydaw_set_pyfx_port(f_result, MKEQ_EQ1_FREQ, 24.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ2_FREQ, 42.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ3_FREQ, 60.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ4_FREQ, 78.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ5_FREQ, 96.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ6_FREQ, 114.0f, 4.0f, 123.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ1_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ2_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ3_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ4_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ5_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ6_RES, 300.0f, 100.0f, 600.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ1_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ2_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ3_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ4_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ5_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_EQ6_GAIN, 0.0f, -240.0f, 240.0f);
    pydaw_set_pyfx_port(f_result, MKEQ_SPECTRUM_ENABLED, 0.0f, 0.0f, 1.0f);

    f_result->cleanup = v_mkeq_cleanup;
    f_result->connect_port = v_mkeq_connect_port;
    f_result->connect_buffer = v_mkeq_connect_buffer;
    f_result->instantiate = g_mkeq_instantiate;
    f_result->panic = v_mkeq_panic;
    f_result->load = v_mkeq_load;
    f_result->set_port_value = v_mkeq_set_port_value;
    f_result->set_cc_map = v_mkeq_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_mkeq_run;
    f_result->on_stop = v_mkeq_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}




/*
void v_mkeq_destructor()
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