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
#include "synth.h"


static void v_mk_vocoder_cleanup(PYFX_Handle instance)
{
    free(instance);
}

static void v_mk_vocoder_set_cc_map(PYFX_Handle instance, char * a_msg)
{
    t_mk_vocoder *plugin = (t_mk_vocoder *)instance;
    v_generic_cc_map_set(&plugin->cc_map, a_msg);
}

static void v_mk_vocoder_panic(PYFX_Handle instance)
{
    //t_mk_vocoder *plugin = (t_mk_vocoder*)instance;
}

static void v_mk_vocoder_on_stop(PYFX_Handle instance)
{
    //t_mk_vocoder *plugin = (t_mk_vocoder*)instance;
}

static void v_mk_vocoder_connect_buffer(PYFX_Handle instance, int a_index,
        MKFLT * DataLocation, int a_is_sidechain)
{
    t_mk_vocoder *plugin = (t_mk_vocoder*)instance;

    if(a_is_sidechain)
    {
        plugin->sc_buffers[a_index] = DataLocation;
    }
    else
    {
        plugin->buffers[a_index] = DataLocation;
    }
}

static void v_mk_vocoder_connect_port(PYFX_Handle instance, int port,
        PYFX_Data * data)
{
    t_mk_vocoder *plugin = (t_mk_vocoder*)instance;

    switch (port)
    {
        case MK_VOCODER_WET: plugin->wet = data; break;
        case MK_VOCODER_MODULATOR: plugin->modulator = data; break;
        case MK_VOCODER_CARRIER: plugin->carrier = data; break;
        default: assert(0); break;
    }
}

static PYFX_Handle g_mk_vocoder_instantiate(PYFX_Descriptor * descriptor,
        int s_rate, fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_mk_vocoder *plugin_data;
    hpalloc((void**)&plugin_data, sizeof(t_mk_vocoder));

    plugin_data->descriptor = descriptor;
    plugin_data->fs = s_rate;
    plugin_data->plugin_uid = a_plugin_uid;
    plugin_data->queue_func = a_queue_func;

    plugin_data->mono_modules =
            v_mk_vocoder_mono_init(plugin_data->fs, plugin_data->plugin_uid);

    plugin_data->port_table = g_get_port_table(
        (void**)plugin_data, descriptor);

    v_cc_map_init(&plugin_data->cc_map);

    return (PYFX_Handle) plugin_data;
}

static void v_mk_vocoder_load(PYFX_Handle instance,
        PYFX_Descriptor * Descriptor, char * a_file_path)
{
    t_mk_vocoder *plugin_data = (t_mk_vocoder*)instance;
    generic_file_loader(instance, Descriptor,
        a_file_path, plugin_data->port_table, &plugin_data->cc_map);
}

static void v_mk_vocoder_set_port_value(PYFX_Handle Instance,
        int a_port, MKFLT a_value)
{
    t_mk_vocoder *plugin_data = (t_mk_vocoder*)Instance;
    plugin_data->port_table[a_port] = a_value;
}

static void v_mk_vocoder_process_midi_event(
    t_mk_vocoder * plugin_data, t_seq_event * a_event)
{

    if (a_event->type == EVENT_CONTROLLER)
    {
        assert(a_event->param >= 1 && a_event->param < 128);

        v_plugin_event_queue_add(&plugin_data->midi_queue,
            EVENT_CONTROLLER, a_event->tick,
            a_event->value, a_event->param);
    }
}


static void v_mk_vocoder_process_midi(
        PYFX_Handle instance, struct ShdsList * events,
        struct ShdsList * atm_events)
{
    t_mk_vocoder *plugin_data = (t_mk_vocoder*)instance;
    register int f_i = 0;
    v_plugin_event_queue_reset(&plugin_data->midi_queue);

    for(f_i = 0; f_i < events->len; ++f_i)
    {
        v_mk_vocoder_process_midi_event(
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


static void v_mk_vocoder_run(
        PYFX_Handle instance, int sample_count,
        struct ShdsList * midi_events, struct ShdsList * atm_events)
{
    t_mk_vocoder *plugin_data = (t_mk_vocoder*)instance;

    t_plugin_event_queue_item * f_midi_item;
    v_mk_vocoder_process_midi(instance, midi_events, atm_events);

    int midi_event_pos = 0;
    int f_i = 0;

    t_smoother_linear * f_wet_smoother =
        &plugin_data->mono_modules->wet_smoother;
    t_smoother_linear * f_carrier_smoother =
        &plugin_data->mono_modules->carrier_smoother;
    t_smoother_linear * f_modulator_smoother =
        &plugin_data->mono_modules->modulator_smoother;

    MKFLT f_amp;

    while(f_i < sample_count)
    {
        while(1)
        {
            f_midi_item = v_plugin_event_queue_iter(
                &plugin_data->midi_queue, f_i);
            if(!f_midi_item)
            {
                break;
            }

            if(f_midi_item->type == EVENT_CONTROLLER)
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

        v_vdr_run(&plugin_data->mono_modules->vocoder,
            plugin_data->sc_buffers[0][f_i], plugin_data->sc_buffers[1][f_i],
            plugin_data->buffers[0][f_i], plugin_data->buffers[1][f_i]);

        v_sml_run(f_carrier_smoother, *plugin_data->carrier);
        f_amp = f_db_to_linear_fast(
            f_carrier_smoother->last_value * 0.1f);
        plugin_data->buffers[0][f_i] *= f_amp;
        plugin_data->buffers[1][f_i] *= f_amp;

        v_sml_run(f_wet_smoother, *plugin_data->wet);
        f_amp = f_db_to_linear_fast(f_wet_smoother->last_value * 0.1f);

        plugin_data->buffers[0][f_i] +=
            plugin_data->mono_modules->vocoder.output0 * f_amp;
        plugin_data->buffers[1][f_i] +=
            plugin_data->mono_modules->vocoder.output1 * f_amp;

        if(*plugin_data->modulator >= -499.0f)
        {
            v_sml_run(f_modulator_smoother, *plugin_data->modulator);
            f_amp = f_db_to_linear_fast(
                f_modulator_smoother->last_value * 0.1f);
            plugin_data->buffers[0][f_i] +=
                plugin_data->sc_buffers[0][f_i] * f_amp;
            plugin_data->buffers[1][f_i] +=
                plugin_data->sc_buffers[1][f_i] * f_amp;
        }

        ++f_i;
    }
}

PYFX_Descriptor *mk_vocoder_PYFX_descriptor()
{
    PYFX_Descriptor *f_result = get_pyfx_descriptor(MK_VOCODER_COUNT);

    set_pyfx_port(f_result, MK_VOCODER_WET, 0.0f, -500.0f, 0.0f);
    set_pyfx_port(f_result, MK_VOCODER_MODULATOR, -500.0f, -500.0f, 0.0f);
    set_pyfx_port(f_result, MK_VOCODER_CARRIER, -500.0f, -500.0f, 0.0f);

    f_result->cleanup = v_mk_vocoder_cleanup;
    f_result->connect_port = v_mk_vocoder_connect_port;
    f_result->connect_buffer = v_mk_vocoder_connect_buffer;
    f_result->instantiate = g_mk_vocoder_instantiate;
    f_result->panic = v_mk_vocoder_panic;
    f_result->load = v_mk_vocoder_load;
    f_result->set_port_value = v_mk_vocoder_set_port_value;
    f_result->set_cc_map = v_mk_vocoder_set_cc_map;

    f_result->API_Version = 1;
    f_result->configure = NULL;
    f_result->run_replacing = v_mk_vocoder_run;
    f_result->run_mixing = NULL;
    f_result->on_stop = v_mk_vocoder_on_stop;
    f_result->offline_render_prep = NULL;

    return f_result;
}


/*
void v_mk_vocoder_destructor()
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
