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

#ifndef PYDAW_PLUGIN_H
#define	PYDAW_PLUGIN_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "plugin.h"
#include <stdlib.h>
#include <assert.h>

#include "plugins/modulex/synth.c"
#include "plugins/euphoria/synth.c"
#include "plugins/way_v/synth.c"
#include "plugins/ray_v2/synth.c"

#include "plugins/mk_delay/synth.c"
#include "plugins/mk_eq/synth.c"
#include "plugins/simple_fader/synth.c"
#include "plugins/simple_reverb/synth.c"
#include "plugins/trigger_fx/synth.c"
#include "plugins/sidechain_comp/synth.c"
#include "plugins/mk_channel/synth.c"
#include "plugins/xfade/synth.c"
#include "plugins/mk_compressor/synth.c"
#include "plugins/mk_vocoder/synth.c"
#include "plugins/mk_limiter/synth.c"


typedef struct
{
    int active;
    int power;
    PYFX_Descriptor *descriptor;
    PYFX_Handle PYFX_handle;
    int uid;
    int pool_uid;
    int atm_count;
    t_pydaw_seq_event * atm_buffer;
    struct ShdsList * atm_list;
    PYFX_Descriptor_Function descfn;
    int mute;
    int solo;
    char padding[CACHE_LINE_SIZE - ((8 * sizeof(int)) + (sizeof(void*) * 4))];
}t_pydaw_plugin;

#ifdef	__cplusplus
}
#endif

PYFX_Descriptor_Function PLUGIN_DESC_FUNCS[] = {
    NULL, //0
    euphoria_PYFX_descriptor, //1
    rayv2_PYFX_descriptor, //2
    wayv_PYFX_descriptor, //3
    modulex_PYFX_descriptor, //4
    mkdelay_PYFX_descriptor, //5
    mkeq_PYFX_descriptor, //6
    sfader_PYFX_descriptor, //7
    sreverb_PYFX_descriptor, //8
    triggerfx_PYFX_descriptor, //9
    scc_PYFX_descriptor, //10
    mkchnl_PYFX_descriptor, //11
    xfade_PYFX_descriptor, //12
    mk_comp_PYFX_descriptor, //13
    mk_vocoder_PYFX_descriptor, //14
    mk_lim_PYFX_descriptor //15
};

NO_OPTIMIZATION void g_pydaw_plugin_init(
        t_pydaw_plugin * f_result,
        int a_sample_rate, int a_index,
        fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    f_result->active = 1;
    f_result->uid = a_index;
    f_result->pool_uid = a_plugin_uid;
    f_result->atm_count = 0;

    int buff_max = 512;

    f_result->atm_list = shds_list_new(buff_max, NULL);

    hpalloc(
        (void**)&f_result->atm_buffer, sizeof(t_pydaw_seq_event) * buff_max);

    f_result->descfn = PLUGIN_DESC_FUNCS[a_index];

    f_result->descriptor = (PYFX_Descriptor*)f_result->descfn();

    assert(f_result->descriptor);

    f_result->PYFX_handle = (PYFX_Handle)f_result->descriptor->instantiate(
            f_result->descriptor, a_sample_rate,
            a_host_wavpool_func, a_plugin_uid, a_queue_func);

    f_result->solo = 0;
    f_result->mute = 0;
    f_result->power = 1;
}

/*
void v_free_pydaw_plugin(t_pydaw_plugin * a_plugin)
{
    if(a_plugin)
    {
        if (a_plugin->descriptor->cleanup)
        {
            a_plugin->descriptor->cleanup(a_plugin->PYFX_handle);
        }

        free(a_plugin);
    }
    else
    {
        printf("Error, attempted to free NULL plugin "
                "with v_free_pydaw_plugin()\n");
    }
}
*/

#endif	/* PYDAW_PLUGIN_H */
