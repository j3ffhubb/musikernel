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

#ifndef KICK_ENV_H
#define	KICK_ENV_H

#define KICK_ENV_SECTIONS 2

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    int sample_counts[KICK_ENV_SECTIONS];
    MKFLT incs[KICK_ENV_SECTIONS];
    int current_env;
    MKFLT sample_rate;
    MKFLT value;
    int counter;
}t_pnv_perc_env;

t_pnv_perc_env * g_pnv_get(MKFLT);
void v_pnv_set(t_pnv_perc_env*, MKFLT, MKFLT, MKFLT, MKFLT, MKFLT);
MKFLT f_pnv_run(t_pnv_perc_env*);

/*
 * void v_pnv_set(t_pnv_perc_env* a_pnv, MKFLT a_t1, MKFLT a_p1,
        MKFLT a_t2, MKFLT a_p2, MKFLT a_note_pitch)
 */
void v_pnv_set(t_pnv_perc_env* a_pnv, MKFLT a_t1, MKFLT a_p1,
        MKFLT a_t2, MKFLT a_p2, MKFLT a_note_pitch)
{
    a_pnv->value = a_p1;
    a_pnv->current_env = 0;
    a_pnv->counter = 0;
    a_pnv->sample_counts[0] = (int)(a_pnv->sample_rate * a_t1);
    a_pnv->sample_counts[1] = (int)(a_pnv->sample_rate * a_t2);
    a_pnv->incs[0] = (a_p2 - a_p1) / a_pnv->sample_counts[0];
    a_pnv->incs[1] = (a_note_pitch - a_p2) / a_pnv->sample_counts[1];
}

MKFLT f_pnv_run(t_pnv_perc_env * a_pnv)
{
    if(a_pnv->current_env < KICK_ENV_SECTIONS)
    {
        a_pnv->value += a_pnv->incs[a_pnv->current_env];

        ++a_pnv->counter;

        if(a_pnv->counter >= a_pnv->sample_counts[a_pnv->current_env])
        {
            a_pnv->counter = 0;
            ++a_pnv->current_env;
        }
    }

    return a_pnv->value;
}

void g_pnv_init(t_pnv_perc_env * f_result, MKFLT a_sr)
{
    f_result->sample_rate = a_sr;

    v_pnv_set(f_result, 0.01f, 75.0f, 0.15f, 48.0f, 24.0f);
}

t_pnv_perc_env * g_pnv_get(MKFLT a_sr)
{
    t_pnv_perc_env * f_result = (t_pnv_perc_env*)malloc(sizeof(t_pnv_perc_env));

    g_pnv_init(f_result, a_sr);

    return f_result;
}

#ifdef	__cplusplus
}
#endif

#endif	/* KICK_ENV_H */

