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

#ifndef AUDIO_XFADE_H
#define	AUDIO_XFADE_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/amp.h"

//#define AXF_DEBUG_MODE

typedef struct st_audio_xfade
{
    MKFLT mid_point;
    MKFLT mid_point_50_minus;
    MKFLT in1_mult;
    MKFLT in2_mult;
#ifdef AXF_DEBUG_MODE
    int debug_counter;
#endif
}t_audio_xfade;

void v_axf_set_xfade(t_audio_xfade *, MKFLT);

/*void v_axf_set_xfade(
 * t_audio_xfade *,
 * MKFLT a_point // 0 to 1
 * )
 */
void v_axf_set_xfade(t_audio_xfade * a_axf_ptr, MKFLT a_point)
{
    a_axf_ptr->in1_mult = 1.0f - a_point;
    a_axf_ptr->in2_mult = a_point;
}

MKFLT f_axf_run_xfade(t_audio_xfade *, MKFLT, MKFLT);


void g_axf_init(t_audio_xfade * f_result, MKFLT a_mid_point)
{
    f_result->mid_point = a_mid_point;
    f_result->mid_point_50_minus = 50.0f - f_result->mid_point;
    f_result->in1_mult = .5f;
    f_result->in2_mult = .5f;
}

/*t_audio_xfade * g_axf_get_audio_xfade
 * (
 * MKFLT a_mid_point //This is the negative gain at 0.5 for both channels.
 *                   //-3 or -6 is a good value
 * )
 */
t_audio_xfade * g_axf_get_audio_xfade(MKFLT a_mid_point)
{
    t_audio_xfade * f_result = (t_audio_xfade*)malloc(sizeof(t_audio_xfade));
    g_axf_init(f_result, a_mid_point);
    return f_result;
}

/* MKFLT f_axf_run_xfade(t_audio_xfade * a_axf_ptr, MKFLT a_in1, MKFLT a_in2)
 */
MKFLT f_axf_run_xfade(t_audio_xfade * a_axf_ptr, MKFLT a_in1, MKFLT a_in2)
{
    return ((a_axf_ptr->in1_mult) * a_in1) + ((a_axf_ptr->in2_mult) * a_in2);
}

#ifdef	__cplusplus
}
#endif

#endif	/* AUDIO_XFADE_H */

