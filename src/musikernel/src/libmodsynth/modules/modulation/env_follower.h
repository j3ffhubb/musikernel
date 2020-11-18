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

#ifndef ENV_FOLLOWER_H
#define	ENV_FOLLOWER_H

#ifdef	__cplusplus
extern "C" {
#endif

//#define ENF_DEBUG_MODE

#include "../filter/one_pole.h"
#include "../../lib/amp.h"

typedef struct st_enf_env_follower
{
    MKFLT input;
    MKFLT output_smoothed;
    t_opl_one_pole * smoother;
#ifdef ENF_DEBUG_MODE
    int debug_counter;
#endif
}t_enf_env_follower;

t_enf_env_follower * g_enf_get_env_follower(MKFLT);
inline void v_enf_run_env_follower(t_enf_env_follower*, MKFLT);

/* inline void v_enf_run_env_follower(
 * t_enf_env_follower * a_enf,
 * MKFLT a_input)  //the signal to follow
 */
inline void v_enf_run_env_follower(t_enf_env_follower * a_enf, MKFLT a_input)
{

    //Get absolute value.  This is much faster than fabs
    if(a_input < 0)
    {
        a_enf->input = a_input * -1;
    }
    else
    {
        a_enf->input = a_input;
    }

    v_opl_run(a_enf->smoother, (a_enf->input));

    /*TODO:  Test the fast l2db function here*/
    a_enf->output_smoothed = f_linear_to_db_fast((a_enf->smoother->output));

#ifdef ENF_DEBUG_MODE
    a_enf->debug_counter = (a_enf->debug_counter) + 1;

    if((a_enf->debug_counter) >= 100000)
    {
        a_enf->debug_counter = 0;

        printf("\n\nEnv Follower info:\n");
        printf("a_enf->input == %f\n", a_enf->input);
        printf("a_enf->output_smoothed == %f\n", a_enf->output_smoothed);
    }
#endif
}

/* t_enf_env_follower * g_enf_get_env_follower(
 * MKFLT a_sr //sample rate
 * )
 */
t_enf_env_follower * g_enf_get_env_follower(MKFLT a_sr)
{
    t_enf_env_follower * f_result = (t_enf_env_follower*)malloc(sizeof(t_enf_env_follower));

    f_result->input = 0;
    f_result->output_smoothed = 0;
    f_result->smoother = g_opl_get_one_pole(a_sr);

    v_opl_set_coeff_hz(f_result->smoother, 10);  //Set the smoother to 10hz.  The reciprocal of the hz value is the total smoother time

#ifdef ENF_DEBUG_MODE
    f_result->debug_counter = 0;
#endif

    return f_result;
}

#ifdef	__cplusplus
}
#endif

#endif	/* ENV_FOLLOWER_H */

