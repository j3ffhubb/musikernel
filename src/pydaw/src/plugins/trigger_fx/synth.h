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

#ifndef TRIGGERFX_SYNTH_H
#define	TRIGGERFX_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define TRIGGERFX_INPUT0  0
#define TRIGGERFX_INPUT1  1
#define TRIGGERFX_OUTPUT0  2
#define TRIGGERFX_OUTPUT1  3

#define TRIGGERFX_FIRST_CONTROL_PORT 4
#define TRIGGERFX_GATE_NOTE 4
#define TRIGGERFX_GATE_MODE 5
#define TRIGGERFX_GATE_WET 6
#define TRIGGERFX_GATE_PITCH 7
#define TRIGGERFX_GLITCH_ON 8
#define TRIGGERFX_GLITCH_NOTE 9
#define TRIGGERFX_GLITCH_TIME 10
#define TRIGGERFX_GLITCH_PB 11

#define TRIGGERFX_LAST_CONTROL_PORT 11
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define TRIGGERFX_COUNT 12

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *gate_note;
    PYFX_Data *gate_mode;
    PYFX_Data *gate_wet;
    PYFX_Data *gate_pitch;

    PYFX_Data *glitch_on;
    PYFX_Data *glitch_note;
    PYFX_Data *glitch_time;
    PYFX_Data *glitch_pb;

    MKFLT fs;
    MKFLT sv_pitch_bend_value;
    t_triggerfx_mono_modules * mono_modules;

    int i_buffer_clear;

    int midi_event_types[200];
    int midi_event_ticks[200];
    MKFLT midi_event_values[200];
    int midi_event_ports[200];
    int midi_event_count;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    MKFLT * port_table;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_triggerfx;

#ifdef	__cplusplus
}
#endif

#endif	/* TRIGGERFX_SYNTH_H */

