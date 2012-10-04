/* -*- c-basic-offset: 4 -*-  vi:set ts=8 sts=4 sw=4: */

/* synth.c

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include <stdint.h>

#include <math.h>
#include <stdio.h>

#include "dssi.h"
#include "ladspa.h"
#include "sequencer.h"

#include "libmodsynth.h"
#include "../../libmodsynth/lib/amp.h"
#include "pydaw.h"

#include "synth.h"
#include "meta.h"

#include <unistd.h>
#include <alsa/asoundlib.h>

static LADSPA_Descriptor *LMSLDescriptor = NULL;
static DSSI_Descriptor *LMSDDescriptor = NULL;

static t_pydaw_data * pydaw_data;

static void run_lms_pydaw(LADSPA_Handle instance, unsigned long sample_count,
		  snd_seq_event_t * events, unsigned long EventCount);


__attribute__ ((visibility("default")))
const LADSPA_Descriptor *ladspa_descriptor(unsigned long index)
{
    switch (index) {
    case 0:
	return LMSLDescriptor;
    default:
	return NULL;
    }
}

__attribute__ ((visibility("default")))
const DSSI_Descriptor *dssi_descriptor(unsigned long index)
{
    switch (index) {
    case 0:
	return LMSDDescriptor;
    default:
	return NULL;
    }
}

static void cleanupLMS(LADSPA_Handle instance)
{
    free(instance);
}

static void connectPortLMS(LADSPA_Handle instance, unsigned long port,
			  LADSPA_Data * data)
{
    t_pydaw_engine *plugin;

    plugin = (t_pydaw_engine *) instance;
        
    if((port >= LMS_INPUT_MIN) && (port < LMS_INPUT_MAX))
    {
        plugin->input_arr[(port - LMS_INPUT_MIN)] = data;
    }
    else
    {        
        switch (port) 
        {     
            case LMS_OUTPUT0: plugin->output0 = data; break;
            case LMS_OUTPUT1: plugin->output1 = data; break;        
        }
    }    
}

static LADSPA_Handle instantiateLMS(const LADSPA_Descriptor * descriptor,
				   unsigned long s_rate)
{
    t_pydaw_engine *plugin_data = (t_pydaw_engine *) malloc(sizeof(t_pydaw_engine));
    pydaw_data = g_pydaw_data_get(s_rate);
    
    plugin_data->fs = s_rate;
            
    /*LibModSynth additions*/
    v_init_lms(s_rate);  //initialize any static variables    
    /*End LibModSynth additions*/
    
    return (LADSPA_Handle) plugin_data;
}

static void activateLMS(LADSPA_Handle instance)
{
    t_pydaw_engine *plugin_data = (t_pydaw_engine *) instance;
        
    plugin_data->mono_modules = v_mono_init((plugin_data->fs));  //initialize all monophonic modules    
}

static void runLMSWrapper(LADSPA_Handle instance,
			 unsigned long sample_count)
{
    run_lms_pydaw(instance, sample_count, NULL, 0);
}

/*This is where parameters are update and the main loop is run.*/
static void run_lms_pydaw(LADSPA_Handle instance, unsigned long sample_count,
		  snd_seq_event_t *events, unsigned long event_count)
{
    t_pydaw_engine *plugin_data = (t_pydaw_engine *) instance;
    /*Define our inputs*/
    
    /*define our outputs*/
    LADSPA_Data *const output0 = plugin_data->output0;    
    LADSPA_Data *const output1 = plugin_data->output1;    
        
    /*Reset our iterators to 0*/    
    int f_i = 0;
    
    pthread_mutex_lock(&pydaw_data->mutex);
    
    pydaw_data->period_size = sample_count;
       
    if((pydaw_data->is_initialized) && ((pydaw_data->playback_mode) > 0))
    {
        while(f_i < PYDAW_MAX_TRACK_COUNT)
        {
            //Process the MIDI events.  It will use something like the below:
            
            /* TODO:
             * 1.  Figure out how to determine which tick of the period to send an event on from the given fractional bar
             * 2.  A next/last fractional bar, that possible event firings must begin between
             * 3.  Persistent note/cc event list iterators
             * 4.  
             */

            /*
            snd_seq_event_t ev;
            int l1;
            double dt;

            for (l1 = 0; l1 < (a_pydaw_data->item_pool[a_item_number]->note_count); l1++) {
              dt = (l1 % 2 == 0) ? (double)swing / 16384.0 : -(double)swing / 16384.0;
              snd_seq_ev_clear(&ev);
              snd_seq_ev_set_note(&ev, 0, sequence[2][l1] + transpose, 127, sequence[1][l1]);
              snd_seq_ev_schedule_tick(&ev, a_pydaw_data->queue_id,  0, a_pydaw_data->tick[a_track_number]);
              snd_seq_ev_set_source(&ev, a_pydaw_data->port_out_id[a_track_number]);
              snd_seq_ev_set_subs(&ev);
              snd_seq_event_output_direct(a_pydaw_data->seq_handle, &ev);
              a_pydaw_data->tick[a_track_number] += (int)((double)sequence[0][l1] * (1.0 + dt));
            }

            //snd_seq_ev_set_controller
             * */

            f_i++;
        }

        pydaw_data->playback_cursor = (pydaw_data->playback_cursor) + ((pydaw_data->playback_inc) * ((double)(sample_count)));
        
        if((pydaw_data->playback_cursor) >= 1.0f)
        {
            pydaw_data->playback_cursor = 0.0f;
            
            if(pydaw_data->loop_mode != PYDAW_LOOP_MODE_BAR)
            {
                pydaw_data->current_bar = (pydaw_data->current_bar) + 1;
                
                if((pydaw_data->current_bar) >= PYDAW_REGION_SIZE)
                {
                    pydaw_data->current_bar = 0;
                    
                    if(pydaw_data->loop_mode != PYDAW_LOOP_MODE_REGION)
                    {
                        pydaw_data->current_region = (pydaw_data->current_region) + 1;
                        
                        if((pydaw_data->current_region) >= PYDAW_MAX_REGION_COUNT)
                        {
                            pydaw_data->playback_mode = 0;
                            pydaw_data->current_region = 0;
                        }
                    }
                }
            }
            
            printf("pydaw_data->current_region == %i, pydaw_data->current_bar == %i\n", (pydaw_data->current_region), (pydaw_data->current_bar));
        }
        
        pydaw_data->current_sample += sample_count;
    }
    pthread_mutex_unlock(&pydaw_data->mutex);
    
    //Mix together the audio input channels from the plugins
    
    plugin_data->i_buffer_clear = 0;
    /*Clear the output buffer*/
    while((plugin_data->i_buffer_clear) < sample_count)
    {
        output0[(plugin_data->i_buffer_clear)] = 0.0f;                        
        output1[(plugin_data->i_buffer_clear)] = 0.0f;     
        plugin_data->i_buffer_clear = (plugin_data->i_buffer_clear) + 1;
    }
    
    int f_i_mix = 0;
    while(f_i_mix < PYDAW_MAX_TRACK_COUNT)
    {
        int f_i2 = f_i_mix + 1;
        plugin_data->i_mono_out = 0;
        /*The main loop where processing happens*/
        while((plugin_data->i_mono_out) < sample_count)
        {
            output0[(plugin_data->i_mono_out)] += *(plugin_data->input_arr[f_i_mix]);
            output1[(plugin_data->i_mono_out)] += *(plugin_data->input_arr[f_i2]);

            plugin_data->i_mono_out = (plugin_data->i_mono_out) + 1;
        }
        f_i_mix += 2;
    }
}

char *pydaw_configure(LADSPA_Handle instance, const char *key, const char *value)
{
    //t_pydaw_engine *plugin_data = (t_pydaw_engine *)instance;
    v_pydaw_parse_configure_message(pydaw_data, key, value);
        
    return NULL;
}

int getControllerLMS(LADSPA_Handle instance, unsigned long port)
{    
    //t_pydaw_engine *plugin_data = (t_pydaw_engine *) instance;
    //return DSSI_CC(i_ccm_get_cc(plugin_data->midi_cc_map, port));
    return 0;     
}

#ifdef __GNUC__
__attribute__((constructor)) void init()
#else
void _init()
#endif
{
    char **port_names;
    LADSPA_PortDescriptor *port_descriptors;
    LADSPA_PortRangeHint *port_range_hints;

    LMSLDescriptor =
	(LADSPA_Descriptor *) malloc(sizeof(LADSPA_Descriptor));
    if (LMSLDescriptor) {
        LMSLDescriptor->UniqueID = LMS_PLUGIN_UUID;
	LMSLDescriptor->Label = LMS_PLUGIN_NAME;
	LMSLDescriptor->Properties = LADSPA_PROPERTY_REALTIME;
	LMSLDescriptor->Name = LMS_PLUGIN_LONG_NAME;
	LMSLDescriptor->Maker = LMS_PLUGIN_DEV;
	LMSLDescriptor->Copyright = "GNU GPL v3";
	LMSLDescriptor->PortCount = LMS_COUNT;

	port_descriptors = (LADSPA_PortDescriptor *)
				calloc(LMSLDescriptor->PortCount, sizeof
						(LADSPA_PortDescriptor));
	LMSLDescriptor->PortDescriptors =
	    (const LADSPA_PortDescriptor *) port_descriptors;

	port_range_hints = (LADSPA_PortRangeHint *)
				calloc(LMSLDescriptor->PortCount, sizeof
						(LADSPA_PortRangeHint));
	LMSLDescriptor->PortRangeHints =
	    (const LADSPA_PortRangeHint *) port_range_hints;

	port_names = (char **) calloc(LMSLDescriptor->PortCount, sizeof(char *));
	LMSLDescriptor->PortNames = (const char **) port_names;

        /* Parameters for input */
        int f_i;
        
        for(f_i = LMS_INPUT_MIN; f_i < LMS_INPUT_MAX; f_i++)
        {
            port_descriptors[f_i] = LADSPA_PORT_INPUT | LADSPA_PORT_AUDIO;
            port_names[f_i] = "Input ";  //TODO:  Give a more descriptive port name
            port_range_hints[f_i].HintDescriptor = 0;
        }
        
	/* Parameters for output */
	port_descriptors[LMS_OUTPUT0] = LADSPA_PORT_OUTPUT | LADSPA_PORT_AUDIO;
	port_names[LMS_OUTPUT0] = "Output 0";
	port_range_hints[LMS_OUTPUT0].HintDescriptor = 0;

        port_descriptors[LMS_OUTPUT1] = LADSPA_PORT_OUTPUT | LADSPA_PORT_AUDIO;
	port_names[LMS_OUTPUT1] = "Output 1";
	port_range_hints[LMS_OUTPUT1].HintDescriptor = 0;
               
        
	LMSLDescriptor->activate = activateLMS;
	LMSLDescriptor->cleanup = cleanupLMS;
	LMSLDescriptor->connect_port = connectPortLMS;
	LMSLDescriptor->deactivate = NULL;
	LMSLDescriptor->instantiate = instantiateLMS;
	LMSLDescriptor->run = runLMSWrapper;
	LMSLDescriptor->run_adding = NULL;
	LMSLDescriptor->set_run_adding_gain = NULL;
    }

    LMSDDescriptor = (DSSI_Descriptor *) malloc(sizeof(DSSI_Descriptor));
    if (LMSDDescriptor) {
	LMSDDescriptor->DSSI_API_Version = 1;
	LMSDDescriptor->LADSPA_Plugin = LMSLDescriptor;
	LMSDDescriptor->configure = pydaw_configure;
	LMSDDescriptor->get_program = NULL;
	LMSDDescriptor->get_midi_controller_for_port = getControllerLMS;
	LMSDDescriptor->select_program = NULL;
	LMSDDescriptor->run_synth = NULL;
	LMSDDescriptor->run_synth_adding = NULL;
	LMSDDescriptor->run_multiple_synths = NULL;
	LMSDDescriptor->run_multiple_synths_adding = NULL;
    }
}

#ifdef __GNUC__
__attribute__((destructor)) void fini()
#else
void _fini()
#endif
{
    if (LMSLDescriptor) {
	free((LADSPA_PortDescriptor *) LMSLDescriptor->PortDescriptors);
	free((char **) LMSLDescriptor->PortNames);
	free((LADSPA_PortRangeHint *) LMSLDescriptor->PortRangeHints);
	free(LMSLDescriptor);
    }
    if (LMSDDescriptor) {
	free(LMSDDescriptor);
    }
}
