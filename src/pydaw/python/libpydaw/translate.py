# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""


try:
    from libpydaw.pydaw_util import INSTALL_PREFIX
except ImportError:
    from pydaw_util import INSTALL_PREFIX

import locale
import gettext
import os

try:
    global_locale, global_encoding = locale.getdefaultlocale()
    print("locale: {}".format(global_locale))
    print("encoding: {}".format(global_encoding))
    global_language = gettext.translation(
        "musikernel3",
        os.path.join(INSTALL_PREFIX, "share", "locale"),
        [global_locale])
    print("global_language.info: {}".format(global_language.info()))
    global_language.install()
    print("Installed language for {}".format(global_locale))
    if not "_" in globals():
        print("'_' not defined by Python gettext module, setting to global_language.gettext")
        _ = global_language.gettext
except Exception as ex:
    print("Exception while setting locale, falling back to English (hopefully):\n".format(ex))

if not "_" in globals():
    print("'_' not defined by Python gettext module, setting to lambda x: x")
    _ = lambda x: x
