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

#ifndef PANNER2_H
#define	PANNER2_H

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT gainL, gainR;
}t_pn2_panner2;


#ifdef	__cplusplus
}
#endif

void g_pn2_init(t_pn2_panner2 * self)
{
    self->gainL = 1.0f;
    self->gainR = 1.0f;
}

void v_pn2_set(t_pn2_panner2 * self, MKFLT a_pan, MKFLT a_law)
{
    if(a_pan == 0.0f)
    {
        self->gainL = f_db_to_linear_fast(a_law);
        self->gainR = self->gainL;
    }
    else if(a_pan == -1.0f)
    {
        self->gainL = 1.0f;
        self->gainR = 0.0f;
    }
    else if(a_pan == 1.0f)
    {
        self->gainL = 0.0f;
        self->gainR = 1.0f;
    }
    else if(a_pan < 0.0f)
    {
        self->gainL = f_db_to_linear_fast((1.0f + a_pan) * a_law);
        self->gainR = f_db_to_linear_fast((-1.0f * a_pan) * - 24.0f);
    }
    else
    {
        self->gainL = f_db_to_linear_fast(a_pan * - 24.0f);
        self->gainR = f_db_to_linear_fast((1.0f - a_pan) * a_law);
    }
}

#endif	/* PANNER2_H */

