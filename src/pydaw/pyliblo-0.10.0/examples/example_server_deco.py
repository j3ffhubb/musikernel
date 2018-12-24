#!/usr/bin/env python

from __future__ import print_function
from liblo import *
import sys

# raw_input renamed to input in python3
try:
    input = raw_input
except NameError:
    pass

class MyServer(ServerThread):
    def __init__(self):
        ServerThread.__init__(self, 1234)

    @make_method('/foo', 'ifs')
    def foo_callback(self, path, args):
        i, f, s = args
        print("received message '%s' with arguments: %d, %f, %s" % (path, i, f, s))

    @make_method(None, None)
    def fallback(self, path, args):
        print("received unknown message '%s'" % path)

try:
    server = MyServer()
except ServerError as err:
    print(err)
    sys.exit()

server.start()
input("press enter to quit...\n")
