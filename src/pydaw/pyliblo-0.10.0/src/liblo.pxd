#
# pyliblo - Python bindings for the liblo OSC library
#
# Copyright (C) 2007-2011  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of the
# License, or (at your option) any later version.
#

from libc.stdint cimport int32_t, uint32_t, int64_t, uint8_t
from libc.stdio cimport const_char


cdef extern from 'lo/lo.h':
    # type definitions
    ctypedef void *lo_server
    ctypedef void *lo_server_thread
    ctypedef void *lo_method
    ctypedef void *lo_address
    ctypedef void *lo_message
    ctypedef void *lo_blob
    ctypedef void *lo_bundle

    ctypedef struct lo_timetag:
        uint32_t sec
        uint32_t frac

    ctypedef union lo_arg:
        int32_t i
        int64_t h
        float f
        double d
        unsigned char c
        char s
        uint8_t m[4]
        lo_timetag t

    cdef enum:
        LO_DEFAULT
        LO_UDP
        LO_UNIX
        LO_TCP

    ctypedef void(*lo_err_handler)(int num, const_char *msg, const_char *where)
    ctypedef int(*lo_method_handler)(const_char *path, const_char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
    ctypedef int(*lo_bundle_start_handler)(lo_timetag time, void *user_data)
    ctypedef int(*lo_bundle_end_handler)(void *user_data)

    # send
    int lo_send_message_from(lo_address targ, lo_server serv, char *path, lo_message msg)
    int lo_send_bundle_from(lo_address targ, lo_server serv, lo_bundle b)

    # server
    lo_server lo_server_new_with_proto(char *port, int proto, lo_err_handler err_h)
    void lo_server_free(lo_server s)
    char *lo_server_get_url(lo_server s)
    int lo_server_get_port(lo_server s)
    int lo_server_get_protocol(lo_server s)
    lo_method lo_server_add_method(lo_server s, char *path, char *typespec, lo_method_handler h, void *user_data)
    void lo_server_del_method(lo_server s, char *path, char *typespec)
    int lo_server_add_bundle_handlers(lo_server s, lo_bundle_start_handler sh, lo_bundle_end_handler eh, void *user_data)
    int lo_server_recv(lo_server s) nogil
    int lo_server_recv_noblock(lo_server s, int timeout) nogil
    int lo_server_get_socket_fd(lo_server s)

    # server thread
    lo_server_thread lo_server_thread_new_with_proto(char *port, int proto, lo_err_handler err_h)
    void lo_server_thread_free(lo_server_thread st)
    lo_server lo_server_thread_get_server(lo_server_thread st)
    void lo_server_thread_start(lo_server_thread st)
    void lo_server_thread_stop(lo_server_thread st)

    # address
    lo_address lo_address_new(char *host, char *port)
    lo_address lo_address_new_with_proto(int proto, char *host, char *port)
    lo_address lo_address_new_from_url(char *url)
    void lo_address_free(lo_address)
    char *lo_address_get_url(lo_address a)
    char *lo_address_get_hostname(lo_address a)
    char *lo_address_get_port(lo_address a)
    int lo_address_get_protocol(lo_address a)
    const_char* lo_address_errstr(lo_address a)

    # message
    lo_message lo_message_new()
    void lo_message_free(lo_message)
    void lo_message_add_int32(lo_message m, int32_t a)
    void lo_message_add_int64(lo_message m, int64_t a)
    void lo_message_add_float(lo_message m, float a)
    void lo_message_add_double(lo_message m, double a)
    void lo_message_add_char(lo_message m, char a)
    void lo_message_add_string(lo_message m, char *a)
    void lo_message_add_symbol(lo_message m, char *a)
    void lo_message_add_true(lo_message m)
    void lo_message_add_false(lo_message m)
    void lo_message_add_nil(lo_message m)
    void lo_message_add_infinitum(lo_message m)
    void lo_message_add_midi(lo_message m, uint8_t a[4])
    void lo_message_add_timetag(lo_message m, lo_timetag a)
    void lo_message_add_blob(lo_message m, lo_blob a)
    lo_address lo_message_get_source(lo_message m)

    # blob
    lo_blob lo_blob_new(int32_t size, void *data)
    void lo_blob_free(lo_blob b)
    void *lo_blob_dataptr(lo_blob b)
    uint32_t lo_blob_datasize(lo_blob b)

    # bundle
    lo_bundle lo_bundle_new(lo_timetag tt)
    void lo_bundle_free(lo_bundle b)
    void lo_bundle_add_message(lo_bundle b, char *path, lo_message m)

    # timetag
    void lo_timetag_now(lo_timetag *t)
