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

#ifndef DRY_WET_H
#define	DRY_WET_H

#include "../../lib/lmalloc.h"
#include "../../lib/amp.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    MKFLT wet_db;
    MKFLT wet_linear;
    MKFLT dry_db;
    MKFLT dry_linear;
    MKFLT output;
}t_dw_dry_wet;

inline void v_dw_set_dry_wet(t_dw_dry_wet*,MKFLT,MKFLT);
inline void v_dw_run_dry_wet(t_dw_dry_wet*,MKFLT,MKFLT);
t_dw_dry_wet* g_dw_get_dry_wet();

/*inline void v_dw_set_dry_wet(
 * t_dw_dry_wet* a_dw,
 * MKFLT a_dry_db, //dry value in decibels, typically -50 to 0
 * MKFLT a_wet_db) //wet value in decibels, typically -50 to 0
 */
inline void v_dw_set_dry_wet(t_dw_dry_wet* a_dw,MKFLT a_dry_db,MKFLT a_wet_db)
{
    if((a_dw->dry_db) != (a_dry_db))
    {
        a_dw->dry_db = a_dry_db;
        a_dw->dry_linear = f_db_to_linear(a_dry_db);
    }

    if((a_dw->wet_db) != (a_wet_db))
    {
        a_dw->wet_db = a_wet_db;
        a_dw->wet_linear = f_db_to_linear(a_wet_db);
    }
}

/* inline void v_dw_run_dry_wet(
 * t_dw_dry_wet* a_dw,
 * MKFLT a_dry, //dry signal
 * MKFLT a_wet) //wet signal
 */
inline void v_dw_run_dry_wet(t_dw_dry_wet* a_dw, MKFLT a_dry, MKFLT a_wet)
{
    a_dw->output = ((a_dw->dry_linear) * a_dry) + ((a_dw->wet_linear) * a_wet);
}

t_dw_dry_wet* g_dw_get_dry_wet()
{
    t_dw_dry_wet* f_result;

    lmalloc((void**)&f_result, sizeof(t_dw_dry_wet));

    f_result->wet_db = -50.0f;
    f_result->wet_linear = 0.0f;
    f_result->dry_db = 0.0f;
    f_result->dry_linear = 1.0f;
    f_result->output = 0.0f;

    return f_result;
}


#ifdef	__cplusplus
}
#endif

#endif	/* DRY_WET_H */

