/* 
 * File:   main.c
 * Author: Jeff Hubbard
 * 
 * 
 *
 * Created on March 12, 2012, 7:46 PM
 */

#include <stdio.h>
#include <stdlib.h>

#include "../../plugins/pydaw/src/synth.c"
#include <dssi.h>
#include "ladspa_ports.h"
#include <unistd.h>
#include <alsa/asoundlib.h>

#define DEBUGGER_SIMULATE_EXTERNAL_MIDI
#define DEBUGGER_SIMULATE_RECORD

int main(int argc, char** argv) 
{
    v_pydaw_constructor();

    const LADSPA_Descriptor * f_ldesc = ladspa_descriptor(0);
    const DSSI_Descriptor * f_ddesc = dssi_descriptor(0);
    LADSPA_Handle f_handle =  f_ldesc->instantiate(f_ldesc, 44100);
    f_ldesc->activate(f_handle);

    t_pydaw_engine * f_engine = (t_pydaw_engine*)f_handle;
        
    //It's not necessary to call this, it gets called anyways at startup...  Only use it to load an alternate project
    //v_open_project(pydaw_data, "/home/bob/dssi/pydaw/default-project");    

    f_engine->output0 = (LADSPA_Data*)malloc(sizeof(LADSPA_Data) * 8192);
    f_engine->output1 = (LADSPA_Data*)malloc(sizeof(LADSPA_Data) * 8192);
    
    float * f_control_ins = (float*)malloc(sizeof(float) * 3000);
    set_ladspa_ports(f_ddesc, f_handle, f_control_ins);
    
    int f_i = 0;
    
    snd_seq_event_t * f_midi_events = (snd_seq_event_t*)malloc(sizeof(snd_seq_event_t) * 512);
    snd_seq_ev_clear(&f_midi_events[0]);
    snd_seq_ev_set_noteon(&f_midi_events[0], 0, 66, 66);
    f_midi_events[0].time.tick = 0;
    snd_seq_ev_clear(&f_midi_events[1]);
    snd_seq_ev_set_controller(&f_midi_events[1], 0, 1, 100);
    f_midi_events[1].time.tick = 5;
    snd_seq_ev_clear(&f_midi_events[2]);
    snd_seq_ev_set_pitchbend(&f_midi_events[2], 0, 1000);
    f_midi_events[2].time.tick = 10;
    snd_seq_ev_clear(&f_midi_events[3]);
    snd_seq_ev_set_noteoff(&f_midi_events[3], 0, 66, 0);
    f_midi_events[2].time.tick = 1000;

#ifdef DEBUGGER_SIMULATE_RECORD
    v_set_playback_mode(pydaw_data, 2, 0, 0);
#endif
    
    //Run it a few times to get the kinks out...  Ideally this shouldn't have to be done, though...
    while(f_i < 100)
    {
#ifdef DEBUGGER_SIMULATE_EXTERNAL_MIDI
        f_ddesc->run_synth(f_handle, 4096, f_midi_events, 4);
#else
        f_ddesc->run_synth(f_handle, 4096, NULL, 0);
#endif
        f_i++;
    }

#ifdef DEBUGGER_SIMULATE_RECORD
    v_set_playback_mode(pydaw_data, 0, 0, 0);
#endif
    
    v_pydaw_offline_render(pydaw_data, 0, 0, 1, 2, "test.wav");
    
    return 0; //(EXIT_SUCCESS);
}

