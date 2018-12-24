#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from distutils.command.build_scripts import build_scripts
from distutils import util, log

try:
    from setuptools import setup, Extension
    args = {
        'test_suite': 'test',
        'zip_safe': False,
    }
except ImportError:
    from distutils.core import setup, Extension
    args = {}

from Cython.Distutils import build_ext


class build_scripts_rename(build_scripts):
    def copy_scripts(self):
        build_scripts.copy_scripts(self)
        # remove the .py extension from scripts
        for s in self.scripts:
            f = util.convert_path(s)
            before = os.path.join(self.build_dir, os.path.basename(f))
            after = os.path.splitext(before)[0]
            log.info("renaming %s -> %s" % (before, after))
            os.rename(before, after)


cmdclass = {
    'build_scripts': build_scripts_rename,
    'build_ext': build_ext,
}

ext_modules = [
    Extension(
        'liblo',
        ['src/liblo.pyx'],
        extra_compile_args = [
            '-fno-strict-aliasing',
            '-Werror-implicit-function-declaration',
            '-Wfatal-errors',
        ],
        libraries = ['lo'],
    )
]


setup(
    name = 'pyliblo',
    version = '0.10.0',
    author = 'Dominic Sacré',
    author_email = 'dominic.sacre@gmx.de',
    url = 'http://das.nasophon.de/pyliblo/',
    description = 'Python bindings for the liblo OSC library',
    license = 'LGPL',
    scripts = [
        'scripts/send_osc.py',
        'scripts/dump_osc.py',
    ],
    data_files = [
        ('share/man/man1', [
            'scripts/send_osc.1',
            'scripts/dump_osc.1',
        ]),
    ],
    cmdclass = cmdclass,
    ext_modules = ext_modules,
    **args
)
