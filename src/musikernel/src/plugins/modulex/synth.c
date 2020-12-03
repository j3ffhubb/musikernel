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

#include "../../libmodsynth/modules/delay/reverb.h"

#include "synth.h"

int MODULEX_AMORITIZER = 0;

static void v_modulex_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_modulex_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_modulex *plugin = (t_modulex *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_modulex_panic(PYFX_Handle instance)
{
    //t_modulex *plugin = (t_modulex*)instance;
}

static void v_modulex_on_stop(PYFX_Handle instance)
{
    //t_modulex *plugin = (t_modulex*)instance;
}

static void v_modulex_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }
    t_modulex *plugin = (t_modulex*)instance;

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

static void v_modulex_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_modulex *plugin;

    plugin = (t_modulex *) instance;

    switch (port)
    {
        case MODULEX_FX0_KNOB0: plugin->fx_knob0[0] = data; break;
        case MODULEX_FX0_KNOB1:	plugin->fx_knob1[0] = data; break;
        case MODULEX_FX0_KNOB2: plugin->fx_knob2[0] = data; break;
        case MODULEX_FX0_COMBOBOX: plugin->fx_combobox[0] = data; break;

        case MODULEX_FX1_KNOB0: plugin->fx_knob0[1] = data; break;
        case MODULEX_FX1_KNOB1:	plugin->fx_knob1[1] = data; break;
        case MODULEX_FX1_KNOB2: plugin->fx_knob2[1] = data; break;
        case MODULEX_FX1_COMBOBOX: plugin->fx_combobox[1] = data; break;

        case MODULEX_FX2_KNOB0: plugin->fx_knob0[2] = data; break;
        case MODULEX_FX2_KNOB1:	plugin->fx_knob1[2] = data; break;
        case MODULEX_FX2_KNOB2: plugin->fx_knob2[2] = data; break;
        case MODULEX_FX2_COMBOBOX: plugin->fx_combobox[2] = data; break;

        case MODULEX_FX3_KNOB0: plugin->fx_knob0[3] = data; break;
        case MODULEX_FX3_KNOB1:	plugin->fx_knob1[3] = data; break;
        case MODULEX_FX3_KNOB2: plugin->fx_knob2[3] = data; break;
        case MODULEX_FX3_COMBOBOX: plugin->fx_combobox[3] = data; break;

        case MODULEX_FX4_KNOB0: plugin->fx_knob0[4] = data; break;
        case MODULEX_FX4_KNOB1:	plugin->fx_knob1[4] = data; break;
        case MODULEX_FX4_KNOB2: plugin->fx_knob2[4] = data; break;
        case MODULEX_FX4_COMBOBOX: plugin->fx_combobox[4] = data; break;

        case MODULEX_FX5_KNOB0: plugin->fx_knob0[5] = data; break;
        case MODULEX_FX5_KNOB1:	plugin->fx_knob1[5] = data; break;
        case MODULEX_FX5_KNOB2: plugin->fx_knob2[5] = data; break;
        case MODULEX_FX5_COMBOBOX: plugin->fx_combobox[5] = data; break;

        case MODULEX_FX6_KNOB0: plugin->fx_knob0[6] = data; break;
        case MODULEX_FX6_KNOB1:	plugin->fx_knob1[6] = data; break;
        case MODULEX_FX6_KNOB2: plugin->fx_knob2[6] = data; break;
        case MODULEX_FX6_COMBOBOX: plugin->fx_combobox[6] = data; break;

        case MODULEX_FX7_KNOB0: plugin->fx_knob0[7] = data; break;
        case MODULEX_FX7_KNOB1:	plugin->fx_knob1[7] = data; break;
        case MODULEX_FX7_KNOB2: plugin->fx_knob2[7] = data; break;
        case MODULEX_FX7_COMBOBOX: plugin->fx_combobox[7] = data; break;
    }
}

static PYFX_Handle g_modulex_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_modulex *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_modulex));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules =
            v_modulex_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->i_slow_index =
            MODULEX_SLOW_INDEX_ITERATIONS + MODULEX_AMORITIZER;

    ++MODULEX_AMORITIZER;
    if(MODULEX_AMORITIZER >= MODULEX_SLOW_INDEX_ITERATIONS)
    {
        MODULEX_AMORITIZER = 0;
    }

    plugin_data->is_on = 0;

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_modulex_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_modulex *plugin_data = (t_modulex*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_modulex_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_modulex *plugin_data = (t_modulex*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static void v_modulex_check_if_on(t_modulex *plugin_data)
{
    register int f_i = 0;

    while(f_i < 8)
    {
        plugin_data->mono_modules->fx_func_ptr[f_i] =
            g_mf3_get_function_pointer((int)(*(plugin_data->fx_combobox[f_i])));

        if(plugin_data->mono_modules->fx_func_ptr[f_i] != v_mf3_run_off)
        {
            plugin_data->is_on = 1;
        }

        ++f_i;
    }
}

static void v_modulex_process_midi_event(
    t_modulex * plugin_data, t_seq_event * a_event)
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

        if(!plugin_data->is_on)
        {
            v_modulex_check_if_on(plugin_data);

            //Meaning that we now have set the port anyways because the
            //main loop won't be running
            if(!plugin_data->is_on)
            {
                plugin_data->port_table[plugin_data->midi_event_ports[
                        plugin_data->midi_event_count]] =
                        plugin_data->midi_event_values[
                        plugin_data->midi_event_count];
            }
        }

        ++plugin_data->midi_event_count;
    }
}

static void v_modulex_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList *atm_events)
{
    t_modulex *plugin_data = (t_modulex*)instance;
    t_mf3_multi * f_fx;

    t_seq_event **events = (t_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int event_pos;
    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    for(event_pos = 0; event_pos < event_count; ++event_pos)
    {
        v_modulex_process_midi_event(plugin_data, events[event_pos]);
    }

    register int f_i = 0;

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

    if(plugin_data->i_slow_index >= MODULEX_SLOW_INDEX_ITERATIONS)
    {
        plugin_data->i_slow_index -= MODULEX_SLOW_INDEX_ITERATIONS;
        plugin_data->is_on = 0;
        v_modulex_check_if_on(plugin_data);
    }
    else
    {
        ++plugin_data->i_slow_index;
    }

    f_i = 0;

    if(plugin_data->is_on)
    {
        int i_mono_out = 0;

        while((i_mono_out) < sample_count)
        {
            while(midi_event_pos < plugin_data->midi_event_count &&
                plugin_data->midi_event_ticks[midi_event_pos] == i_mono_out)
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
                &plugin_data->atm_queue, i_mono_out,
                plugin_data->port_table);

            plugin_data->mono_modules->current_sample0 =
                    plugin_data->output0[(i_mono_out)];
            plugin_data->mono_modules->current_sample1 =
                    plugin_data->output1[(i_mono_out)];

            f_i = 0;

            while(f_i < 8)
            {
                if(plugin_data->mono_modules->fx_func_ptr[f_i] != v_mf3_run_off)
                {
                    f_fx = &plugin_data->mono_modules->multieffect[f_i];
                    v_sml_run(&plugin_data->mono_modules->smoothers[f_i][0],
                            *plugin_data->fx_knob0[f_i]);
                    v_sml_run(&plugin_data->mono_modules->smoothers[f_i][1],
                            *plugin_data->fx_knob1[f_i]);
                    v_sml_run(&plugin_data->mono_modules->smoothers[f_i][2],
                            *plugin_data->fx_knob2[f_i]);

                    v_mf3_set(f_fx,
                    plugin_data->mono_modules->smoothers[f_i][0].last_value,
                    plugin_data->mono_modules->smoothers[f_i][1].last_value,
                    plugin_data->mono_modules->smoothers[f_i][2].last_value);

                    plugin_data->mono_modules->fx_func_ptr[f_i](
                        f_fx,
                        (plugin_data->mono_modules->current_sample0),
                        (plugin_data->mono_modules->current_sample1));

                    plugin_data->mono_modules->current_sample0 = f_fx->output0;
                    plugin_data->mono_modules->current_sample1 = f_fx->output1;
                }
                ++f_i;
            }

            plugin_data->output0[(i_mono_out)] =
                    (plugin_data->mono_modules->current_sample0);
            plugin_data->output1[(i_mono_out)] =
                    (plugin_data->mono_modules->current_sample1);

            ++i_mono_out;
        }
    }
}

PYFX_Descriptor *modulex_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = get_pyfx_descriptor(MODULEX_COUNT);

    set_pyfx_port(f_result, MODULEX_FX0_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX0_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX0_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX0_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX1_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX1_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX1_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX1_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX2_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX2_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX2_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX2_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX3_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX3_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX3_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX3_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX4_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX4_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX4_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX4_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX5_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX5_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX5_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX5_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX6_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX6_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX6_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX6_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);
    set_pyfx_port(f_result, MODULEX_FX7_KNOB0, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX7_KNOB1, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX7_KNOB2, 64.0f, 0.0f, 127.0f);
    set_pyfx_port(f_result, MODULEX_FX7_COMBOBOX, 0.0f, 0.0f, MULTIFX3KNOB_MAX_INDEX);


    f_result->cleanup = v_modulex_cleanup;
    f_result->connect_port = v_modulex_connect_port;
    f_result->connect_buffer = v_modulex_connect_buffer;
    f_result->instantiate = g_modulex_instantiate;
    f_result->panic = v_modulex_panic;
    f_result->load = v_modulex_load;
    f_result->set_port_value = v_modulex_set_port_value;
    f_result->set_cc_map = v_modulex_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_modulex_run;
    f_result->on_stop = v_modulex_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}




/*
void v_modulex_destructor()
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
