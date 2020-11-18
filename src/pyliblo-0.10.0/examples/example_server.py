#!/usr/bin/env python

from __future__ import print_function
import liblo, sys

# create server, listening on port 1234
try:
    server = liblo.Server(1234)
except liblo.ServerError as err:
    print(err)
    sys.exit()

def foo_bar_callback(path, args):
    i, f = args
    print("received message '%s' with arguments '%d' and '%f'" % (path, i, f))

def foo_baz_callback(path, args, types, src, data):
    print("received message '%s'" % path)
    print("blob contains %d bytes, user data was '%s'" % (len(args[0]), data))

def fallback(path, args, types, src):
    print("got unknown message '%s' from '%s'" % (path, src.url))
    for a, t in zip(args, types):
        print("argument of type '%s': %s" % (t, a))

# register method taking an int and a float
server.add_method("/foo/bar", 'if', foo_bar_callback)

# register method taking a blob, and passing user data to the callback
server.add_method("/foo/baz", 'b', foo_baz_callback, "blah")

# register a fallback for unhandled messages
server.add_method(None, None, fallback)

# loop and dispatch messages every 100ms
while True:
    server.recv(100)

