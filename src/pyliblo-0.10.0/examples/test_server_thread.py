#!/usr/bin/env python

from __future__ import print_function
import liblo
import time

st = liblo.ServerThread()
print("Created Server Thread on Port", st.port)

def foo_cb(path, args, types):
    print("foo_cb():")
    for a, t in zip(args, types):
        print("received argument %s of type %s" % (a, t))

def bar_cb(path, args, types, src):
    print("bar_cb():")
    print("message from", src.url)
    print("typespec:", types)
    for a, t in zip(args, types):
        print("received argument %s of type %s" % (a, t))

class Blah:
    def __init__(self, x):
        self.x = x
    def baz_cb(self, path, args, types, src, user_data):
        print("baz_cb():")
        print(args[0])
        print("self.x is", self.x, ", user data was", user_data)

st.add_method('/foo', 'ifs', foo_cb)
st.add_method('/bar', 'hdc', bar_cb)

b = Blah(123)
st.add_method('/baz', 'b', b.baz_cb, 456)

st.start()

liblo.send(st.port, "/foo", 123, 456.789, "buh!")
l = 1234567890123456
liblo.send(st.port, "/bar", l, 666, ('c', "x"))

time.sleep(1)
st.stop()
st.start()

liblo.send(st.port, "/baz", [1,2,3,4,5,6,7,8,9,10])

time.sleep(1)
