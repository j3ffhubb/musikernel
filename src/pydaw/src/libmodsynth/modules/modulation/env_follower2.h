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

#ifndef ENF_ENV_FOLLOWER_H
#define	ENF_ENV_FOLLOWER_H

#include "../../lib/lms_math.h"
#include <math.h>

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT attack;
    MKFLT release;
    MKFLT a_coeff;
    MKFLT r_coeff;
    MKFLT envelope;
    MKFLT sample_rate;
}t_enf2_env_follower;

#ifdef	__cplusplus
}
#endif


void g_enf_init(t_enf2_env_follower* self, MKFLT a_sr)
{
    self->envelope = 0.0f;
    self->sample_rate = a_sr;
    self->attack = -1.234f;
    self->release = -1.234f;
}

void v_enf_set(t_enf2_env_follower* self, MKFLT a_attack, MKFLT a_release)
{
    if(self->attack != a_attack)
    {
        self->attack = a_attack;
        self->a_coeff = exp(log(0.01f) / ( a_attack * self->sample_rate));
    }

    if(self->release != a_release)
    {
        self->release = a_release;
        self->r_coeff = exp(log(0.01f) / ( a_release * self->sample_rate));
    }
}

void v_enf_run(t_enf2_env_follower* self, MKFLT a_input)
{
    MKFLT tmp = f_lms_abs(a_input);
    if(tmp > self->envelope)
    {
        self->envelope = self->a_coeff * (self->envelope - tmp) + tmp;
    }
    else
    {
        self->envelope = self->r_coeff * (self->envelope - tmp) + tmp;
    }

    self->envelope = f_remove_denormal(self->envelope);
}


#endif	/* ENF_ENV_FOLLOWER_H */

