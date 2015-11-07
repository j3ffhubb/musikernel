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

#include "synth.h"

#define TRIGGERFX_EVENT_GATE_ON 1001
#define TRIGGERFX_EVENT_GATE_OFF 1002
#define TRIGGERFX_EVENT_GLITCH_ON 1003
#define TRIGGERFX_EVENT_GLITCH_OFF 1004


static void v_triggerfx_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_triggerfx_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_triggerfx *plugin = (t_triggerfx *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_triggerfx_panic(PYFX_Handle instance)
{
    t_triggerfx *plugin = (t_triggerfx*)instance;

    plugin->mono_modules->gate_on = 0.0f;
    plugin->mono_modules->glitch_on = 0.0f;

    v_adsr_kill(&plugin->mono_modules->glitch.adsr);
}

static void v_triggerfx_on_stop(PYFX_Handle instance)
{
    t_triggerfx *plugin = (t_triggerfx*)instance;

    plugin->mono_modules->gate_on = 0.0f;
    plugin->mono_modules->glitch_on = 0.0f;
    v_glc_glitch_v2_release(&plugin->mono_modules->glitch);
    plugin->sv_pitch_bend_value = 0.0f;
}

static void v_triggerfx_connect_buffer(PYFX_Handle instance, int a_index,
        float * DataLocation, int a_is_sidechain)
{
    if(a_is_sidechain)
    {
        return;
    }

    t_triggerfx *plugin = (t_triggerfx*)instance;

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

static void v_triggerfx_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_triggerfx *plugin;

    plugin = (t_triggerfx *) instance;

    switch (port)
    {
        case TRIGGERFX_GATE_MODE: plugin->gate_mode = data; break;
        case TRIGGERFX_GATE_NOTE: plugin->gate_note = data; break;
        case TRIGGERFX_GATE_PITCH: plugin->gate_pitch = data; break;
        case TRIGGERFX_GATE_WET: plugin->gate_wet = data; break;

        case TRIGGERFX_GLITCH_ON: plugin->glitch_on = data; break;
        case TRIGGERFX_GLITCH_NOTE: plugin->glitch_note = data; break;
        case TRIGGERFX_GLITCH_TIME: plugin->glitch_time = data; break;

        case TRIGGERFX_GLITCH_PB: plugin->glitch_pb = data; break;
    }
}

static PYFX_Handle g_triggerfx_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_triggerfx *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_triggerfx));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->sv_pitch_bend_value = 0.0f;

    plugin_data->mono_modules =
        v_triggerfx_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_pydaw_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_triggerfx_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_triggerfx *plugin_data = (t_triggerfx*)instance;
    pydaw_generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_triggerfx_set_port_value(PYFX_Handle Instance,
        int a_port, float a_value)
{
    t_triggerfx *plugin_data = (t_triggerfx*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static inline void v_triggerfx_run_gate(t_triggerfx *plugin_data,
        float a_in0, float a_in1)
{
    v_sml_run(&plugin_data->mono_modules->gate_wet_smoother,
            *plugin_data->gate_wet * 0.01f);
    v_gat_set(&plugin_data->mono_modules->gate, *plugin_data->gate_pitch,
            plugin_data->mono_modules->gate_wet_smoother.last_value);
    v_gat_run(&plugin_data->mono_modules->gate,
            plugin_data->mono_modules->gate_on, a_in0, a_in1);
}

static inline void v_triggerfx_run_glitch(t_triggerfx *plugin_data,
        float a_in0, float a_in1)
{
    v_sml_run(&plugin_data->mono_modules->glitch_time_smoother,
            *plugin_data->glitch_time * 0.01f);
    v_glc_glitch_v2_set(&plugin_data->mono_modules->glitch,
            plugin_data->mono_modules->glitch_time_smoother.last_value,
            plugin_data->mono_modules->pitchbend_smoother.last_value *
            (*plugin_data->glitch_pb));
    v_glc_glitch_v2_run(&plugin_data->mono_modules->glitch, a_in0, a_in1);
}

static void v_triggerfx_process_midi_event(
    t_triggerfx * plugin_data, t_pydaw_seq_event * a_event)
{
    int f_gate_note = (int)*plugin_data->gate_note;
    int f_glitch_note = (int)*plugin_data->glitch_note;

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
    else if (a_event->type == PYDAW_EVENT_NOTEON)
    {
        if(a_event->note == f_gate_note)
        {
            plugin_data->midi_event_types[plugin_data->midi_event_count] =
                    TRIGGERFX_EVENT_GATE_ON;
            plugin_data->midi_event_ticks[plugin_data->midi_event_count] =
                    a_event->tick;
            float f_db = (0.283464567f *  // 1.0f / 127.0f
                ((float)a_event->velocity)) - 28.3464567f;
            plugin_data->midi_event_values[plugin_data->midi_event_count] =
                f_db_to_linear_fast(f_db);

            ++plugin_data->midi_event_count;
        }
        if(a_event->note == f_glitch_note)
        {
            plugin_data->midi_event_types[plugin_data->midi_event_count] =
                    TRIGGERFX_EVENT_GLITCH_ON;
            plugin_data->midi_event_ticks[plugin_data->midi_event_count] =
                    a_event->tick;
            float f_db = (0.283464567f *  // 1.0f / 127.0f
                ((float)a_event->velocity)) - 28.3464567f;
            plugin_data->midi_event_values[plugin_data->midi_event_count] =
                f_db_to_linear_fast(f_db);

            ++plugin_data->midi_event_count;
        }
    }
    else if (a_event->type == PYDAW_EVENT_NOTEOFF)
    {
        if(a_event->note == f_gate_note)
        {
            plugin_data->midi_event_types[plugin_data->midi_event_count] =
                    TRIGGERFX_EVENT_GATE_OFF;
            plugin_data->midi_event_ticks[
                    plugin_data->midi_event_count] = a_event->tick;
            plugin_data->midi_event_values[
                    plugin_data->midi_event_count] = 0.0f;
            ++plugin_data->midi_event_count;
        }
        if(a_event->note == f_glitch_note)
        {
            plugin_data->midi_event_types[plugin_data->midi_event_count] =
                    TRIGGERFX_EVENT_GLITCH_OFF;
            plugin_data->midi_event_ticks[
                    plugin_data->midi_event_count] = a_event->tick;
            plugin_data->midi_event_values[
                    plugin_data->midi_event_count] = 0.0f;
            ++plugin_data->midi_event_count;
        }
    }
    else if (a_event->type == PYDAW_EVENT_PITCHBEND)
    {
        plugin_data->midi_event_types[plugin_data->midi_event_count] =
                PYDAW_EVENT_PITCHBEND;
        plugin_data->midi_event_ticks[plugin_data->midi_event_count] =
                a_event->tick;
        plugin_data->midi_event_values[plugin_data->midi_event_count] =
                0.00012207 * a_event->value;
        ++plugin_data->midi_event_count;
    }
}

static void v_triggerfx_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_triggerfx *plugin_data = (t_triggerfx*)instance;

    t_pydaw_seq_event **events = (t_pydaw_seq_event**)midi_events->data;
    int event_count = midi_events->len;

    int f_i = 0;
    int midi_event_pos = 0;
    plugin_data->midi_event_count = 0;

    int f_gate_on = (int)*plugin_data->gate_mode;
    int f_glitch_on = (int)*plugin_data->glitch_on;

    for(f_i = 0; f_i < event_count; ++f_i)
    {
        v_triggerfx_process_midi_event(plugin_data, events[f_i]);
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
                plugin_data->midi_event_ticks[midi_event_pos] ==
                f_i)
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
            else if(plugin_data->midi_event_types[midi_event_pos] ==
                PYDAW_EVENT_PITCHBEND)
            {
                plugin_data->sv_pitch_bend_value =
                        plugin_data->midi_event_values[midi_event_pos];
            }
            else if(plugin_data->midi_event_types[midi_event_pos] ==
                    TRIGGERFX_EVENT_GATE_ON)
            {
                plugin_data->mono_modules->gate_on =
                        plugin_data->midi_event_values[midi_event_pos];
            }
            else if(plugin_data->midi_event_types[midi_event_pos] ==
                    TRIGGERFX_EVENT_GATE_OFF)
            {
                plugin_data->mono_modules->gate_on =
                        plugin_data->midi_event_values[midi_event_pos];
            }
            else if(plugin_data->midi_event_types[midi_event_pos] ==
                    TRIGGERFX_EVENT_GLITCH_ON)
            {
                plugin_data->mono_modules->glitch_on =
                        plugin_data->midi_event_values[midi_event_pos];
                v_glc_glitch_v2_retrigger(
                        &plugin_data->mono_modules->glitch);
            }
            else if(plugin_data->midi_event_types[midi_event_pos] ==
                    TRIGGERFX_EVENT_GLITCH_OFF)
            {
                plugin_data->mono_modules->glitch_on =
                        plugin_data->midi_event_values[midi_event_pos];
                v_glc_glitch_v2_release(&plugin_data->mono_modules->glitch);
            }

            ++midi_event_pos;
        }

        v_plugin_event_queue_atm_set(
            &plugin_data->atm_queue, f_i, plugin_data->port_table);

        plugin_data->mono_modules->current_sample0 =
                plugin_data->output0[f_i];
        plugin_data->mono_modules->current_sample1 =
                plugin_data->output1[f_i];

        v_sml_run(&plugin_data->mono_modules->pitchbend_smoother,
                (plugin_data->sv_pitch_bend_value));

        if(f_glitch_on &&
        plugin_data->mono_modules->glitch.adsr.stage != ADSR_STAGE_OFF)
        {
            v_triggerfx_run_glitch(plugin_data,
                    plugin_data->mono_modules->current_sample0,
                    plugin_data->mono_modules->current_sample1);
            plugin_data->mono_modules->current_sample0 =
                    plugin_data->mono_modules->glitch.output0;
            plugin_data->mono_modules->current_sample1 =
                    plugin_data->mono_modules->glitch.output1;
        }

        if(f_gate_on)
        {
            v_triggerfx_run_gate(plugin_data,
                    plugin_data->mono_modules->current_sample0,
                    plugin_data->mono_modules->current_sample1);
            plugin_data->mono_modules->current_sample0 =
                    plugin_data->mono_modules->gate.output[0];
            plugin_data->mono_modules->current_sample1 =
                    plugin_data->mono_modules->gate.output[1];
        }

        plugin_data->output0[f_i] =
                (plugin_data->mono_modules->current_sample0);
        plugin_data->output1[f_i] =
                (plugin_data->mono_modules->current_sample1);

        ++f_i;
    }

}

PYFX_Descriptor *triggerfx_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = pydaw_get_pyfx_descriptor(TRIGGERFX_COUNT);

    pydaw_set_pyfx_port(f_result, TRIGGERFX_GATE_NOTE, 120.0f, 0.0f, 120.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GATE_MODE, 0.0f, 0.0f, 2.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GATE_WET, 0.0f, 0.0f, 100.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GATE_PITCH, 60.0f, 20.0f, 120.0f);

    pydaw_set_pyfx_port(f_result, TRIGGERFX_GLITCH_ON, 0.0f, 0.0f, 1.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GLITCH_NOTE, 120.0f, 0.0f, 120.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GLITCH_TIME, 10.0f, 1.0f, 25.0f);
    pydaw_set_pyfx_port(f_result, TRIGGERFX_GLITCH_PB, 0.0f, 0.0f, 36.0f);

    f_result->cleanup = v_triggerfx_cleanup;
    f_result->connect_port = v_triggerfx_connect_port;
    f_result->connect_buffer = v_triggerfx_connect_buffer;
    f_result->instantiate = g_triggerfx_instantiate;
    f_result->panic = v_triggerfx_panic;
    f_result->load = v_triggerfx_load;
    f_result->set_port_value = v_triggerfx_set_port_value;
    f_result->set_cc_map = v_triggerfx_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_triggerfx_run;
    f_result->on_stop = v_triggerfx_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}




/*
void v_triggerfx_destructor()
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