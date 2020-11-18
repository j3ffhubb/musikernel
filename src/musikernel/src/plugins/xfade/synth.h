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

#ifndef XFADE_SYNTH_H
#define	XFADE_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../plugin.h"
#include "libmodsynth.h"

#define XFADE_FIRST_CONTROL_PORT 0
#define XFADE_SLIDER 0
#define XFADE_MIDPOINT 1

#define XFADE_LAST_CONTROL_PORT 1
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define XFADE_COUNT 2

typedef struct
{
    MKFLT * buffers[2];
    MKFLT * sc_buffers[2];
    PYFX_Data *pan;
    PYFX_Data *pan_law;
    MKFLT fs;
    t_xfade_mono_modules * mono_modules;

    int i_mono_out;
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
} t_xfade;

#ifdef	__cplusplus
}
#endif

#endif	/* XFADE_SYNTH_H */

