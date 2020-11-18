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

#ifndef MKCHNL_SYNTH_H
#define	MKCHNL_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../plugin.h"
#include "libmodsynth.h"

#define MKCHNL_FIRST_CONTROL_PORT 0
#define MKCHNL_VOL_SLIDER 0
#define MKCHNL_GAIN 1
#define MKCHNL_PAN 2
#define MKCHNL_LAW 3

#define MKCHNL_LAST_CONTROL_PORT 3
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MKCHNL_COUNT 4

typedef struct
{
    MKFLT * buffers[2];
    PYFX_Data *vol_slider;
    PYFX_Data *gain;
    PYFX_Data *pan;
    PYFX_Data *pan_law;
    MKFLT fs;
    t_mkchnl_mono_modules * mono_modules;

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
} t_mkchnl;

#ifdef	__cplusplus
}
#endif

#endif	/* MKCHNL_SYNTH_H */

