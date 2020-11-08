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

#ifndef SIMPLE_FADER_SYNTH_H
#define	SIMPLE_FADER_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define SFADER_FIRST_CONTROL_PORT 0
#define SFADER_VOL_SLIDER 0

#define SFADER_LAST_CONTROL_PORT 0
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SFADER_COUNT 1

typedef struct
{
    MKFLT * buffers[2];
    PYFX_Data *vol_slider;
    MKFLT fs;
    t_sfader_mono_modules * mono_modules;

    int i_mono_out;
    int i_buffer_clear;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    MKFLT * port_table;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_sfader;

#ifdef	__cplusplus
}
#endif

#endif	/* SIMPLE_FADER_SYNTH_H */

