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

#ifndef SYNTH_H
#define	SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define MODULEX_SLOW_INDEX_ITERATIONS 30

#define MODULEX_FIRST_CONTROL_PORT 4
#define MODULEX_FX0_KNOB0  4
#define MODULEX_FX0_KNOB1  5
#define MODULEX_FX0_KNOB2  6
#define MODULEX_FX0_COMBOBOX 7
#define MODULEX_FX1_KNOB0  8
#define MODULEX_FX1_KNOB1  9
#define MODULEX_FX1_KNOB2  10
#define MODULEX_FX1_COMBOBOX 11
#define MODULEX_FX2_KNOB0  12
#define MODULEX_FX2_KNOB1  13
#define MODULEX_FX2_KNOB2  14
#define MODULEX_FX2_COMBOBOX 15
#define MODULEX_FX3_KNOB0  16
#define MODULEX_FX3_KNOB1  17
#define MODULEX_FX3_KNOB2  18
#define MODULEX_FX3_COMBOBOX 19
#define MODULEX_FX4_KNOB0  20
#define MODULEX_FX4_KNOB1  21
#define MODULEX_FX4_KNOB2  22
#define MODULEX_FX4_COMBOBOX 23
#define MODULEX_FX5_KNOB0  24
#define MODULEX_FX5_KNOB1  25
#define MODULEX_FX5_KNOB2  26
#define MODULEX_FX5_COMBOBOX 27
#define MODULEX_FX6_KNOB0  28
#define MODULEX_FX6_KNOB1  29
#define MODULEX_FX6_KNOB2  30
#define MODULEX_FX6_COMBOBOX 31
#define MODULEX_FX7_KNOB0  32
#define MODULEX_FX7_KNOB1  33
#define MODULEX_FX7_KNOB2  34
#define MODULEX_FX7_COMBOBOX 35

#define MODULEX_LAST_CONTROL_PORT 35
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MODULEX_COUNT 36

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *fx_knob0[8];
    PYFX_Data *fx_knob1[8];
    PYFX_Data *fx_knob2[8];
    PYFX_Data *fx_combobox[8];

    MKFLT fs;
    t_modulex_mono_modules * mono_modules;

    int i_slow_index;
    int is_on;

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
} t_modulex;

#ifdef	__cplusplus
}
#endif

#endif	/* SYNTH_H */

