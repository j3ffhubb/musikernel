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

#ifndef FFTW_LOCK_H
#define	FFTW_LOCK_H

#include <pthread.h>
#include <fftw3.h>

pthread_mutex_t FFTW_LOCK;
int FFTW_LOCK_INIT = 0;

#ifdef MK_USE_DOUBLE
fftw_plan g_fftw_plan_dft_r2c_1d(
#else
fftwf_plan g_fftw_plan_dft_r2c_1d(
#endif
    int a_size,
    MKFLT * a_in,
#ifdef MK_USE_DOUBLE
    fftw_complex * a_out,
#else
    fftwf_complex * a_out,
#endif
    unsigned a_flags
){
#ifdef MK_USE_DOUBLE
    fftw_plan f_result;
#else
    fftwf_plan f_result;
#endif

    if(!FFTW_LOCK_INIT)
    {
        pthread_mutex_init(&FFTW_LOCK, NULL);
        FFTW_LOCK_INIT = 1;
    }

    pthread_mutex_lock(&FFTW_LOCK);
#ifdef MK_USE_DOUBLE
    f_result = fftw_plan_dft_r2c_1d(a_size, a_in, a_out, a_flags);
#else
    f_result = fftwf_plan_dft_r2c_1d(a_size, a_in, a_out, a_flags);
#endif
    pthread_mutex_unlock(&FFTW_LOCK);

    return f_result;
}

#endif	/* FFTW_LOCK_H */

