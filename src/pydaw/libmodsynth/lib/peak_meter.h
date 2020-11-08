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

#ifndef PEAK_METER_H
#define	PEAK_METER_H

#define PEAK_STEP_SIZE 4

#include "lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

// a peak meter
typedef struct
{
    volatile MKFLT value[2];
    int buffer_pos;
    volatile int dirty;
}t_pkm_peak_meter;

// a gain reduction meter
typedef struct
{
    MKFLT gain_redux;
    int counter;
    int count;
    int dirty;
}t_pkm_redux;

#ifdef	__cplusplus
}
#endif

void g_pkm_redux_init(t_pkm_redux * self, MKFLT a_sr)
{
    self->gain_redux = 0.0f;
    self->counter = 0;
    self->count = (int)(a_sr / 30.0f);
}

void v_pkm_redux_lin_reset(t_pkm_redux * self)
{
    self->dirty = 0;
    self->gain_redux = 1.0f;
}

void v_pkm_redux_run(t_pkm_redux * self, MKFLT a_gain)
{
    ++self->counter;
    if(unlikely(self->counter >= self->count))
    {
        self->dirty = 1;
        self->counter = 0;
    }

    if(a_gain < self->gain_redux)
    {
        self->gain_redux = a_gain;
    }
}

void g_pkm_init(t_pkm_peak_meter * f_result)
{
    f_result->value[0] = 0.0f;
    f_result->value[1] = 0.0f;
    f_result->buffer_pos = 0;
    f_result->dirty = 0;
}

t_pkm_peak_meter * g_pkm_get()
{
    t_pkm_peak_meter * f_result;
    lmalloc((void**)(&f_result), sizeof(t_pkm_peak_meter));

    g_pkm_init(f_result);

    return f_result;
}

static inline MKFLT f_pkm_compare(MKFLT a_audio, MKFLT a_peak)
{
    MKFLT f_value = a_audio;

    if(a_audio < 0.0f)
    {
        f_value = a_audio * -1.0f;
    }

    if(f_value > a_peak)
    {
        return f_value;
    }
    else
    {
        return a_peak;
    }
}

/* For the host to call after reading the peak value
 */
void v_pkm_reset(t_pkm_peak_meter * self)
{
    self->dirty = 1;
}

void v_pkm_run(t_pkm_peak_meter * self,
        MKFLT * a_in0, MKFLT * a_in1, int a_count)
{
    if(self->dirty)
    {
        self->dirty = 0;
        self->value[0] = 0.0f;
        self->value[1] = 0.0f;
    }
    self->buffer_pos = 0;
    while(self->buffer_pos < a_count)
    {
        self->value[0] = f_pkm_compare(a_in0[self->buffer_pos], self->value[0]);
        self->value[1] = f_pkm_compare(a_in1[self->buffer_pos], self->value[1]);
        self->buffer_pos += PEAK_STEP_SIZE;
    }
}

#endif	/* PEAK_METER_H */

