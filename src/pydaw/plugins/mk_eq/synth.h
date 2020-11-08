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

#ifndef MKEQ_SYNTH_H
#define	MKEQ_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define MKEQ_FIRST_CONTROL_PORT 4

#define MKEQ_EQ1_FREQ 4
#define MKEQ_EQ1_RES 5
#define MKEQ_EQ1_GAIN 6
#define MKEQ_EQ2_FREQ 7
#define MKEQ_EQ2_RES 8
#define MKEQ_EQ2_GAIN 9
#define MKEQ_EQ3_FREQ 10
#define MKEQ_EQ3_RES 11
#define MKEQ_EQ3_GAIN 12
#define MKEQ_EQ4_FREQ 13
#define MKEQ_EQ4_RES 14
#define MKEQ_EQ4_GAIN 15
#define MKEQ_EQ5_FREQ 16
#define MKEQ_EQ5_RES 17
#define MKEQ_EQ5_GAIN 18
#define MKEQ_EQ6_FREQ 19
#define MKEQ_EQ6_RES 20
#define MKEQ_EQ6_GAIN 21
#define MKEQ_SPECTRUM_ENABLED 22

#define MKEQ_LAST_CONTROL_PORT 22
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MKEQ_COUNT 23

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *eq_freq[6];
    PYFX_Data *eq_res[6];
    PYFX_Data *eq_gain[6];
    PYFX_Data *spectrum_analyzer_on;

    MKFLT fs;
    t_mkeq_mono_modules * mono_modules;

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
} t_mkeq;

#ifdef	__cplusplus
}
#endif

#endif	/* MKEQ_SYNTH_H */

