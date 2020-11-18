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

#ifndef SREVERB_SYNTH_H
#define	SREVERB_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../plugin.h"
#include "libmodsynth.h"

#define SREVERB_FIRST_CONTROL_PORT 0

#define SREVERB_REVERB_TIME 0
#define SREVERB_REVERB_WET 1
#define SREVERB_REVERB_COLOR 2
#define SREVERB_REVERB_DRY 3
#define SREVERB_REVERB_PRE_DELAY 4
#define SREVERB_REVERB_HP 5

#define SREVERB_LAST_CONTROL_PORT 5
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SREVERB_COUNT 6

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *reverb_time;
    PYFX_Data *reverb_dry;
    PYFX_Data *reverb_wet;
    PYFX_Data *reverb_color;
    PYFX_Data *reverb_hp;
    PYFX_Data *reverb_predelay;

    MKFLT fs;
    t_sreverb_mono_modules * mono_modules;

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
} t_sreverb;

#ifdef	__cplusplus
}
#endif

#endif	/* SREVERB_SYNTH_H */

