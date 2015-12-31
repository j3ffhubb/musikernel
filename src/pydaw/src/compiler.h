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

#ifndef MK_COMPILER_H
#define	MK_COMPILER_H

#include <assert.h>
#include <stdlib.h>
#include <sndfile.h>
#include <stdio.h>

#include "libshds.h"

#ifdef __APPLE__

    #include <libkern/OSAtomic.h>

    #define pthread_spinlock_t OSSpinLock
    #define pthread_spin_lock OSSpinLockLock
    #define pthread_spin_unlock OSSpinLockUnlock

    void pthread_spin_init(OSSpinLock * a_lock, void * a_opts)
    {
        *a_lock = 0;
    }

#endif

#if defined(__linux__) && !defined(MK_DLL)
    #include <lo/lo.h>
#endif

#if !defined(CACHE_LINE_SIZE)
    #define CACHE_LINE_SIZE 64
    #warning "CACHE_LINE_SIZE not defined by compiler defaulting to 64"
#elif (CACHE_LINE_SIZE < 64) || (CACHE_LINE_SIZE > 128)
    #undef CACHE_LINE_SIZE
    #define CACHE_LINE_SIZE 64
    #warning "CACHE_LINE_SIZE < 64 or > 128, using 64 as the cache line size"
#endif

#define likely(x)   __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)

// LLVM defines __GNUC__ , but doesn't implement it's built-ins
// GCC offers no defines that only mean it's compiled with GCC

#ifdef __clang__
    #define assume_aligned(x, y) (x)
    #define NO_OPTIMIZATION
#else
    #define assume_aligned(x, y) __builtin_assume_aligned((x), (y))
    #define NO_OPTIMIZATION __attribute__((optimize("-O0")))
#endif


#define prefetch __builtin_prefetch
#define PREFETCH_STRIDE 64

#ifdef __linux__

inline void prefetch_range(void *addr, size_t len)
{
    char *cp;
    char *end = (char*)addr + len;

    for(cp = (char*)addr; cp < end; cp += PREFETCH_STRIDE)
    {
        prefetch(cp);
    }
}

#endif

#if defined(__MINGW32__) && !defined(_WIN32)
#define _WIN32
#endif

// Use forward-slash on all OS
#define PATH_SEP "/"

#if defined(_WIN32)
    #define REAL_PATH_SEP "\\"
    char * get_home_dir()
    {
        char * f_result = getenv("USERPROFILE");
        assert(f_result);
        return f_result;
    }
#else
    #define REAL_PATH_SEP "/"
    char * get_home_dir()
    {
        char * f_result = getenv("HOME");
        assert(f_result);
        return f_result;
    }
#endif

/* Intended to be similar to Python's os.path.join */
void path_join(char * a_result, int num, char ** a_str_list)
{
    int f_i, f_i2, f_pos;
    f_pos = 0;
    char * f_str;
    char f_chr;

    for (f_i = 0; f_i < num; ++f_i)
    {
        if(f_i)
        {
            a_result[f_pos] = PATH_SEP[0];
            ++f_pos;
        }

        f_str = a_str_list[f_i];

        for(f_i2 = 0; ; ++f_i2)
        {
            f_chr = f_str[f_i2];
            if(f_chr == '\0')
            {
                break;
            }
            a_result[f_pos] = f_chr;
            ++f_pos;
        }
    }

    a_result[f_pos] = '\0';
}


#endif	/* MK_COMPILER_H */

