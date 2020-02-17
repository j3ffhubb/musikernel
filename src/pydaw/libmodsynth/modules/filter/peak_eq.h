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

#ifndef PEAK_EQ_H
#define	PEAK_EQ_H

#include "../../lib/pitch_core.h"
#include "../../lib/amp.h"
#include "../../constants.h"
#include "../../lib/denormal.h"
#include "../../lib/lmalloc.h"
#include <math.h>

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    float BW, dB, pitch, exp_value, exp_db, d, B, d_times_B,
            w, w2, wQ, y2_0, y2_1, FIR_out_0, FIR_out_1, w2p1,
            coeff0, coeff1, coeff2, pi_div_sr;
    float input0, input1, in0_m1, in0_m2, in1_m1, in1_m2;
    float output0, output1, out0_m1, out0_m2, out1_m1, out1_m2;
    float warp_input, warp_input_squared, warp_input_tripled,
            warp_outstream0, warp_outstream1, warp_output;

    float coeff1_x_out_m1_0, coeff2_x_out_m2_0, iir_output0,
            coeff1_x_out_m1_1, coeff2_x_out_m2_1, iir_output1;

    float last_pitch;
}t_pkq_peak_eq;


inline void v_pkq_calc_coeffs(t_pkq_peak_eq*, float, float, float);
inline void v_pkq_run(t_pkq_peak_eq*, float, float);
void v_pkq_free(t_pkq_peak_eq*);

void v_pkq_free(t_pkq_peak_eq * a_pkq)
{
    free(a_pkq);
}

/* inline void v_pkq_calc_coeffs(
 * t_pkq_peak_eq *a_pkq,
 * float a_pitch,
 * float a_bw,
 * float a_db)
 */
inline void v_pkq_calc_coeffs(t_pkq_peak_eq * a_pkq,
        float a_pitch, float a_bw, float a_db)
{
    if((a_db != (a_pkq->dB)) || (a_bw != (a_pkq->BW)))
    {
        a_pkq->BW = a_bw;
        a_pkq->dB = a_db;
        a_pkq->exp_value = exp((a_pkq->BW)*log(1.421f));
        a_pkq->exp_db = exp((a_pkq->dB)*log(1.061f));

        a_pkq->d = (((a_pkq->exp_value) * (a_pkq->exp_value)) - 1.0f) /
                ((a_pkq->exp_value) * (a_pkq->exp_db));

        a_pkq->B = ((a_pkq->exp_db) * (a_pkq->exp_db)) - 1.0f;

        a_pkq->d_times_B = (a_pkq->d) * (a_pkq->B);
    }

    if(a_pitch != a_pkq->last_pitch)
    {
        a_pkq->last_pitch = a_pitch;
        a_pkq->warp_input =
            f_pit_midi_note_to_hz_fast(a_pitch) * (a_pkq->pi_div_sr);
        a_pkq->warp_input_squared = (a_pkq->warp_input) * (a_pkq->warp_input);
        a_pkq->warp_input_tripled =
                (a_pkq->warp_input_squared) * (a_pkq->warp_input);
        a_pkq->warp_outstream0 = (a_pkq->warp_input_squared) *
                (a_pkq->warp_input_tripled) * 0.133333f;
        a_pkq->warp_outstream1 = (a_pkq->warp_input_tripled) * 0.333333f;
        a_pkq->w = (a_pkq->warp_outstream0) + (a_pkq->warp_outstream1) +
                (a_pkq->warp_input);
    }


    a_pkq->w2 = (a_pkq->w) * (a_pkq->w);
    a_pkq->wQ = (a_pkq->w) * (a_pkq->d);


    a_pkq->w2p1 = (a_pkq->w2) + 1.0f;
    a_pkq->coeff0 = 1.0f / ((a_pkq->w2p1) + (a_pkq->wQ));
    a_pkq->coeff1 = ((a_pkq->w2) - 1.0f) * 2.0f;
    a_pkq->coeff2 = (a_pkq->w2p1) - (a_pkq->wQ);
}

inline void v_pkq_run(t_pkq_peak_eq * a_pkq,float a_in0, float a_in1)
{
    a_pkq->in0_m2 = (a_pkq->in0_m1);
    a_pkq->in0_m1 = a_in0;

    a_pkq->y2_0 = a_pkq->in0_m2;
    a_pkq->FIR_out_0 = (a_in0 - (a_pkq->y2_0)) * (a_pkq->w);

    a_pkq->in1_m2 = (a_pkq->in1_m1);
    a_pkq->in1_m1 = a_in1;

    a_pkq->y2_1 = a_pkq->in1_m2;
    a_pkq->FIR_out_1 = (a_in1 - (a_pkq->y2_1)) * (a_pkq->w);

    a_pkq->coeff1_x_out_m1_0 = (a_pkq->FIR_out_0) -
            ((a_pkq->coeff1) * (a_pkq->out0_m1));
    a_pkq->coeff2_x_out_m2_0 = (a_pkq->coeff1_x_out_m1_0) -
            ((a_pkq->coeff2) * (a_pkq->out0_m2));
    a_pkq->iir_output0 = f_remove_denormal(
            (a_pkq->coeff2_x_out_m2_0) * (a_pkq->coeff0));
    a_pkq->output0 = ((a_pkq->d_times_B) * (a_pkq->iir_output0)) + a_in0;

    a_pkq->coeff1_x_out_m1_1 = (a_pkq->FIR_out_1) -
            ((a_pkq->coeff1) * (a_pkq->out1_m1));
    a_pkq->coeff2_x_out_m2_1 = (a_pkq->coeff1_x_out_m1_1) -
            ((a_pkq->coeff2) * (a_pkq->out1_m2));
    a_pkq->iir_output1 =
            f_remove_denormal((a_pkq->coeff2_x_out_m2_1) * (a_pkq->coeff0));
    a_pkq->output1 = ((a_pkq->d_times_B) * (a_pkq->iir_output1)) + a_in1;


    a_pkq->out0_m2 = (a_pkq->out0_m1);
    a_pkq->out0_m1 = (a_pkq->iir_output0);

    a_pkq->out1_m2 = (a_pkq->out1_m1);
    a_pkq->out1_m1 = (a_pkq->iir_output1);
}

void g_pkq_init(t_pkq_peak_eq * f_result, float a_sample_rate)
{
    f_result->B = 0.0f;
    f_result->FIR_out_0 = 0.0f;
    f_result->FIR_out_1 = 0.0f;
    f_result->BW = 0.0f;
    f_result->coeff1 = 0.0f;
    f_result->coeff2 = 0.0f;
    f_result->d = 0.0f;
    f_result->dB = 0.0f;
    f_result->d_times_B = 0.0f;
    f_result->exp_db = 0.0f;
    f_result->exp_value = 0.0f;
    f_result->in0_m1 = 0.0f;
    f_result->in0_m2 = 0.0f;
    f_result->in1_m1 = 0.0f;
    f_result->in1_m2 = 0.0f;
    f_result->input0 = 0.0f;
    f_result->input1 = 0.0f;
    f_result->out0_m1 = 0.0f;
    f_result->out0_m2 = 0.0f;
    f_result->out1_m1 = 0.0f;
    f_result->out1_m2 = 0.0f;
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;
    f_result->pi_div_sr = PI / a_sample_rate;
    f_result->pitch = 66.0f;
    f_result->coeff0 = 0.0f;
    f_result->warp_input = 0.0f;
    f_result->warp_input_squared = 0.0f;
    f_result->warp_input_tripled = 0.0f;
    f_result->warp_output = 0.0f;
    f_result->warp_outstream0 = 0.0f;
    f_result->warp_outstream1 = 0.0f;
    f_result->w = 0.0f;
    f_result->w2 = 0.0f;
    f_result->w2p1 = 0.0f;
    f_result->wQ = 0.0f;
    f_result->y2_0 = 0.0f;
    f_result->y2_1 = 0.0f;
    f_result->last_pitch = -452.66447f;
}


typedef struct
{
    t_pkq_peak_eq eqs[6];
    float * knobs[6][3];  //freq, bw, gain
    float output0;
    float output1;
}t_eq6;

void g_eq6_init(t_eq6 * f_result, float a_sr)
{
    f_result->output0 = 0.0f;
    f_result->output1 = 0.0f;

    int f_i = 0;

    while(f_i < 6)
    {
        g_pkq_init(&f_result->eqs[f_i], a_sr);
        ++f_i;
    }
}

void v_eq6_connect_port(t_eq6 * a_eq6, int a_port, float * a_ptr)
{
    int f_eq_num = a_port / 3;
    int f_knob_num = a_port % 3;

    a_eq6->knobs[f_eq_num][f_knob_num] = a_ptr;
}

inline void v_eq6_set(t_eq6 *a_eq6)
{
    int f_i;

    for(f_i = 0; f_i < 6; ++f_i)
    {
        if(*a_eq6->knobs[f_i][2] != 0.0f)
        {
            v_pkq_calc_coeffs(&a_eq6->eqs[f_i],
                    *a_eq6->knobs[f_i][0],
                    *a_eq6->knobs[f_i][1] * 0.01f,
                    *a_eq6->knobs[f_i][2] * 0.1f);
        }
    }
}

inline void v_eq6_run(t_eq6 *a_eq6, float a_input0, float a_input1)
{
    int f_i;

    a_eq6->output0 = a_input0;
    a_eq6->output1 = a_input1;

    for(f_i = 0; f_i < 6; ++f_i)
    {
        if(*a_eq6->knobs[f_i][2] != 0.0f)
        {
            v_pkq_run(&a_eq6->eqs[f_i], a_eq6->output0, a_eq6->output1);

            a_eq6->output0 = a_eq6->eqs[f_i].output0;
            a_eq6->output1 = a_eq6->eqs[f_i].output1;
        }
    }
}


#ifdef	__cplusplus
}
#endif

#endif	/* PEAK_EQ_H */

