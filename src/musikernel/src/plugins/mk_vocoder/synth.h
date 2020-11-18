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

#ifndef MK_VOCODER_SYNTH_H
#define	MK_VOCODER_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../plugin.h"
#include "libmodsynth.h"

#define MK_VOCODER_WET 0
#define MK_VOCODER_MODULATOR 1
#define MK_VOCODER_CARRIER 2

#define MK_VOCODER_FIRST_CONTROL_PORT 0

#define MK_VOCODER_LAST_CONTROL_PORT 2
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MK_VOCODER_COUNT 3

typedef struct
{
    PYFX_Data * wet;
    PYFX_Data * modulator;
    PYFX_Data * carrier;
    MKFLT * buffers[2];
    MKFLT * sc_buffers[2];
    MKFLT fs;
    t_mk_vocoder_mono_modules * mono_modules;

    int i_mono_out;
    int i_buffer_clear;

    t_plugin_event_queue midi_queue;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    MKFLT * port_table;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_mk_vocoder;

#ifdef	__cplusplus
}
#endif

#endif	/* MK_VOCODER_SYNTH_H */

