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

#ifndef MK_COMP_SYNTH_H
#define	MK_COMP_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../plugin.h"
#include "libmodsynth.h"
#include "../../libmodsynth/modules/dynamics/compressor.h"

#define MK_COMP_FIRST_CONTROL_PORT 0

#define MK_COMP_THRESHOLD 0
#define MK_COMP_RATIO 1
#define MK_COMP_KNEE 2
#define MK_COMP_ATTACK 3
#define MK_COMP_RELEASE 4
#define MK_COMP_GAIN 5
#define MK_COMP_MODE 6
#define MK_COMP_RMS_TIME 7
#define MK_COMP_UI_MSG_ENABLED 8

#define MK_COMP_LAST_CONTROL_PORT 8
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MK_COMP_COUNT 9

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *threshold;
    PYFX_Data *ratio;
    PYFX_Data *knee;
    PYFX_Data *attack;
    PYFX_Data *release;
    PYFX_Data *gain;
    PYFX_Data *mode;
    PYFX_Data *rms_time;
    PYFX_Data *peak_meter;


    MKFLT fs;
    t_mk_comp_mono_modules * mono_modules;

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
    char ui_msg_buff[64];
} t_mk_comp;

#ifdef	__cplusplus
}
#endif

#endif	/* MK_COMP_SYNTH_H */

