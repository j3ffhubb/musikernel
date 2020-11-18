#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# pyliblo - Python bindings for the liblo OSC library
#
# Copyright (C) 2007-2015  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import unittest
import re
import time
import sys
import liblo


def matchHost(host, regex):
    r = re.compile(regex)
    return r.match(host) != None


class Arguments:
    def __init__(self, path, args, types, src, data):
        self.path = path
        self.args = args
        self.types = types
        self.src = src
        self.data = data


class ServerTestCaseBase(unittest.TestCase):
    def setUp(self):
        self.cb = None

    def callback(self, path, args, types, src, data):
        self.cb = Arguments(path, args, types, src, data)

    def callback_dict(self, path, args, types, src, data):
        if self.cb == None:
            self.cb = { }
        self.cb[path] = Arguments(path, args, types, src, data)


class ServerTestCase(ServerTestCaseBase):
    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.server = liblo.Server('1234')

    def tearDown(self):
        del self.server

    def testPort(self):
        self.assertEqual(self.server.port, 1234)

    def testURL(self):
        self.assertTrue(matchHost(self.server.url, 'osc\.udp://.*:1234/'))

    def testSendInt(self):
        self.server.add_method('/foo', 'i', self.callback, "data")
        self.server.send('1234', '/foo', 123)
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.path, '/foo')
        self.assertEqual(self.cb.args[0], 123)
        self.assertEqual(self.cb.types, 'i')
        self.assertEqual(self.cb.data, "data")
        self.assertTrue(matchHost(self.cb.src.url, 'osc\.udp://.*:1234/'))

    def testSendBlob(self):
        self.server.add_method('/blob', 'b', self.callback)
        self.server.send('1234', '/blob', [4, 8, 15, 16, 23, 42])
        self.assertTrue(self.server.recv())
        if sys.hexversion < 0x03000000:
            self.assertEqual(self.cb.args[0], [4, 8, 15, 16, 23, 42])
        else:
            self.assertEqual(self.cb.args[0], b'\x04\x08\x0f\x10\x17\x2a')

    def testSendVarious(self):
        self.server.add_method('/blah', 'ihfdscb', self.callback)
        if sys.hexversion < 0x03000000:
            self.server.send(1234, '/blah', 123, 2**42, 123.456, 666.666, "hello", ('c', 'x'), (12, 34, 56))
        else:
            self.server.send(1234, '/blah', 123, ('h', 2**42), 123.456, 666.666, "hello", ('c', 'x'), (12, 34, 56))
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.types, 'ihfdscb')
        self.assertEqual(len(self.cb.args), len(self.cb.types))
        self.assertEqual(self.cb.args[0], 123)
        self.assertEqual(self.cb.args[1], 2**42)
        self.assertAlmostEqual(self.cb.args[2], 123.456, 3)
        self.assertAlmostEqual(self.cb.args[3], 666.666, 3)
        self.assertEqual(self.cb.args[4], "hello")
        self.assertEqual(self.cb.args[5], 'x')
        if sys.hexversion < 0x03000000:
            self.assertEqual(self.cb.args[6], [12, 34, 56])
        else:
            self.assertEqual(self.cb.args[6], b'\x0c\x22\x38')

    def testSendOthers(self):
        self.server.add_method('/blubb', 'tmSTFNI', self.callback)
        self.server.send(1234, '/blubb', ('t', 666666.666), ('m', (1, 2, 3, 4)), ('S', 'foo'), True, ('F',), None, ('I',))
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.types, 'tmSTFNI')
        self.assertAlmostEqual(self.cb.args[0], 666666.666)
        self.assertEqual(self.cb.args[1], (1, 2, 3, 4))
        self.assertEqual(self.cb.args[2], 'foo')
        self.assertEqual(self.cb.args[3], True)
        self.assertEqual(self.cb.args[4], False)
        self.assertEqual(self.cb.args[5], None)
        self.assertEqual(self.cb.args[6], float('inf'))

    def testSendMessage(self):
        self.server.add_method('/blah', 'is', self.callback)
        m = liblo.Message('/blah', 42, 'foo')
        self.server.send(1234, m)
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.types, 'is')
        self.assertEqual(self.cb.args[0], 42)
        self.assertEqual(self.cb.args[1], 'foo')

    def testSendLong(self):
        l = 1234567890123456
        self.server.add_method('/long', 'h', self.callback)
        m = liblo.Message('/long', l)
        self.server.send(1234, m)
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.types, 'h')
        self.assertEqual(self.cb.args[0], l)

    def testSendingLongAsIntOverflows(self):
        l = 1234567890123456
        with self.assertRaises(OverflowError):
            liblo.Message('/long', (l, 'i'))

    def testSendBundle(self):
        self.server.add_method('/foo', 'i', self.callback_dict)
        self.server.add_method('/bar', 's', self.callback_dict)
        self.server.send(1234, liblo.Bundle(
            liblo.Message('/foo', 123),
            liblo.Message('/bar', "blubb")
        ))
        self.assertTrue(self.server.recv(100))
        self.assertEqual(self.cb['/foo'].args[0], 123)
        self.assertEqual(self.cb['/bar'].args[0], "blubb")

    def testSendTimestamped(self):
        self.server.add_method('/blubb', 'i', self.callback)
        d = 1.23
        t1 = time.time()
        b = liblo.Bundle(liblo.time() + d)
        b.add('/blubb', 42)
        self.server.send(1234, b)
        while not self.cb:
            self.server.recv(1)
        t2 = time.time()
        self.assertAlmostEqual(t2 - t1, d, 1)

    def testSendInvalid(self):
        with self.assertRaises(TypeError):
            self.server.send(1234, '/blubb', ('x', 'y'))

    def testRecvTimeout(self):
        t1 = time.time()
        self.assertFalse(self.server.recv(500))
        t2 = time.time()
        self.assertLess(t2 - t1, 0.666)

    def testRecvImmediate(self):
        t1 = time.time()
        self.assertFalse(self.server.recv(0))
        t2 = time.time()
        self.assertLess(t2 - t1, 0.01)

    def testMethodAfterFree(self):
        self.server.free()
        with self.assertRaises(RuntimeError):
            self.server.recv()

    def testBundleCallbacksFire(self):
        def bundle_start_cb(timestamp, user_data):
            self.assertIsInstance(timestamp, float)
            user_data.append('start')
        def bundle_end_cb(user_data):
            user_data.append('end')
        bundle_data = []
        self.server.add_bundle_handlers(bundle_start_cb, bundle_end_cb, bundle_data)
        self.testSendBundle()
        self.assertEqual(bundle_data, ['start', 'end'])


class ServerCreationTestCase(unittest.TestCase):
    def testNoPermission(self):
        with self.assertRaises(liblo.ServerError):
            s = liblo.Server('22')

    def testRandomPort(self):
        s = liblo.Server()
        self.assertGreaterEqual(s.port, 1024)
        self.assertLessEqual(s.port, 65535)

    def testPort(self):
        s = liblo.Server(1234)
        t = liblo.Server('5678')
        self.assertEqual(s.port, 1234)
        self.assertEqual(t.port, 5678)
        self.assertTrue(matchHost(s.url, 'osc\.udp://.*:1234/'))

    def testPortProto(self):
        s = liblo.Server(1234, liblo.TCP)
        self.assertTrue(matchHost(s.url, 'osc\.tcp://.*:1234/'))


class ServerTCPTestCase(ServerTestCaseBase):
    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.server = liblo.Server('1234', liblo.TCP)

    def tearDown(self):
        del self.server

    def testSendReceive(self):
        self.server.add_method('/foo', 'i', self.callback)
        liblo.send(self.server.url, '/foo', 123)
        self.assertTrue(self.server.recv())
        self.assertEqual(self.cb.path, '/foo')
        self.assertEqual(self.cb.args[0], 123)
        self.assertEqual(self.cb.types, 'i')

#    def testNotReachable(self):
#        with self.assertRaises(IOError):
#            self.server.send('osc.tcp://192.168.23.42:4711', '/foo', 23, 42)


class ServerThreadTestCase(ServerTestCaseBase):
    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.server = liblo.ServerThread('1234')

    def tearDown(self):
        del self.server

    def testSendAndReceive(self):
        self.server.add_method('/foo', 'i', self.callback)
        self.server.send('1234', '/foo', 42)
        self.server.start()
        time.sleep(0.2)
        self.server.stop()
        self.assertEqual(self.cb.args[0], 42)


class DecoratorTestCase(unittest.TestCase):
    class TestServer(liblo.Server):
        def __init__(self):
            liblo.Server.__init__(self, 1234)

        @liblo.make_method('/foo', 'ibm')
        def foo_cb(self, path, args, types, src, data):
            self.cb = Arguments(path, args, types, src, data)

    def setUp(self):
        self.server = self.TestServer()

    def tearDown(self):
        del self.server

    def testSendReceive(self):
        liblo.send(1234, '/foo', 42, ('b', [4, 8, 15, 16, 23, 42]), ('m', (6, 6, 6, 0)))
        self.assertTrue(self.server.recv())
        self.assertEqual(self.server.cb.path, '/foo')
        self.assertEqual(len(self.server.cb.args), 3)


class AddressTestCase(unittest.TestCase):
    def testPort(self):
        a = liblo.Address(1234)
        b = liblo.Address('5678')
        self.assertEqual(a.port, 1234)
        self.assertEqual(b.port, 5678)
        self.assertEqual(a.url, 'osc.udp://localhost:1234/')

    def testUrl(self):
        a = liblo.Address('osc.udp://foo:1234/')
        self.assertEqual(a.url, 'osc.udp://foo:1234/')
        self.assertEqual(a.hostname, 'foo')
        self.assertEqual(a.port, 1234)
        self.assertEqual(a.protocol, liblo.UDP)

    def testHostPort(self):
        a = liblo.Address('foo', 1234)
        self.assertEqual(a.url, 'osc.udp://foo:1234/')

    def testHostPortProto(self):
        a = liblo.Address('foo', 1234, liblo.TCP)
        self.assertEqual(a.url, 'osc.tcp://foo:1234/')


if __name__ == "__main__":
    unittest.main()
