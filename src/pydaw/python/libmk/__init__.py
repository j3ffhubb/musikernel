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

import datetime
import os
from libpydaw import pydaw_util

if pydaw_util.IS_LINUX and not pydaw_util.IS_ENGINE_LIB:
    from libpydaw import liblo

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from libpydaw.translate import _

#Circular dependency, so it assigns a pointer to itself here when loaded
#import mkplugins
#overriding this:
mkplugins = None

# These are dynamically assigned by musikernel.py so that
# hosts can access them from this module
MAIN_WINDOW = None
HOST_MODULES = None
APP = None
TRANSPORT = None
IS_PLAYING = False
IS_RECORDING = False
IPC = None
IPC_ENABLED = False
OSC = None
PROJECT = None
PLUGIN_UI_DICT = None
CURRENT_HOST = 0
TOOLTIPS_ENABLED = pydaw_util.get_file_setting("tooltips", int, 1)
MEMORY_ENTROPY = datetime.timedelta(minutes=0)
MEMORY_ENTROPY_LIMIT = datetime.timedelta(minutes=30)
MEMORY_ENTROPY_UIDS = set()

def clean_wav_pool():
    f_result = set()
    for f_host in HOST_MODULES:
        f_result.update(f_host.active_wav_pool_uids())

    if pydaw_util.USE_HUGEPAGES:
        for f_uid in (x for x in f_result if x in MEMORY_ENTROPY_UIDS):
            MEMORY_ENTROPY_UIDS.remove(f_uid)
    #invert
    f_len = len(PROJECT.get_wavs_dict())
    f_result = [x for x in range(f_len) if x not in f_result]
    print("clean_wav_pool '{}', '{}'".format(f_len, f_result))
    if f_result:
        f_msg = "|".join(str(x) for x in sorted(f_result))
        IPC.clean_wavpool(f_msg)

    if pydaw_util.USE_HUGEPAGES:
        for f_uid in (x for x in f_result if x not in MEMORY_ENTROPY_UIDS):
            MEMORY_ENTROPY_UIDS.add(f_uid)
            f_sg = PROJECT.get_sample_graph_by_uid(f_uid)
            f_delta = datetime.timedelta(seconds=f_sg.length_in_seconds)
            if add_entropy(f_delta):
                restart_engine()
                break


def add_entropy(a_timedelta):
    """ Use this to restart the engine and clean up the wav pool memory

        This returns a bool, to avoid restarting the engine at an
        inopportune time.  It is the responsibility of the caller to
        also call
    """
    global MEMORY_ENTROPY
    MEMORY_ENTROPY += a_timedelta
    if MEMORY_ENTROPY > MEMORY_ENTROPY_LIMIT:
        print("Recording entropy exceeded, restarting engine "
            "to clean and defragment memory")
        MEMORY_ENTROPY = datetime.timedelta(minutes=0)
        return True
    else:
        return False

def restart_engine():
    if pydaw_util.IS_ENGINE_LIB:
        print("Not restarting engine because the engine is running "
            "as a shared library")
    else:
        close_pydaw_engine()
        reopen_pydaw_engine()

def prepare_to_quit():
    global MAIN_WINDOW, TRANSPORT, IPC, OSC, PROJECT
    MAIN_WINDOW = TRANSPORT = IPC = OSC = PROJECT = None

def set_window_title():
    if not MAIN_WINDOW:
        return
    MAIN_WINDOW.setWindowTitle('MusiKernel - {}'.format(
        os.path.join(
            PROJECT.project_folder, '{}.{}'.format(
                PROJECT.project_file,
                pydaw_util.global_pydaw_version_string))))

def pydaw_print_generic_exception(a_ex):
    QMessageBox.warning(
        MAIN_WINDOW, _("Warning"),
        _("The following error happened:\n{}").format(a_ex))

class AbstractIPC:
    """ Abstract class containing the minimum contract
        to run MK Plugins for host communication to the
        MusiKernel engine
    """
    def __init__(self, a_with_audio=False,
             a_configure_path="/musikernel/dawnext"):
        if not a_with_audio:
            self.with_osc = False
            return
        else:
            self.with_osc = True
            self.m_suppressHostUpdate = False
            self.configure_path = a_configure_path

    def send_configure(self, key, value):
        if not IPC_ENABLED and key != "exit":
            print("IPC_ENABLED == False, "
                "Would've sent configure message: key: \""
                "{}\" value: \"{}\"".format(key, value))
            return
        if pydaw_util.IS_ENGINE_LIB:
            pydaw_util.engine_lib_configure(self.configure_path, key, value)
        elif self.with_osc:
            liblo.send(OSC, self.configure_path, key, value)
        else:
            print("Running standalone UI without OSC.  "
                "Would've sent configure message: key: \""
                "{}\" value: \"{}\"".format(key, value))


class AbstractProject:
    """ Abstract class containing the minimum contract
        to run MK Plugins for host project file saving
    """
    def __init__(self):
        self.plugin_pool_folder = None

    def create_file(self, a_folder, a_file, a_text):
        """  Call save_file only if the file doesn't exist... """
        if not os.path.isfile(os.path.join(
        self.project_folder, a_folder, a_file)):
            self.save_file(a_folder, a_file, a_text)
        else:
            assert(False)

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        """ Writes a file to disk and updates the project
            history to reflect the changes
        """
        f_full_path = os.path.join(
            *(str(x) for x in (self.project_folder, a_folder, a_file)))
        if not a_force_new and os.path.isfile(f_full_path):
            f_old = pydaw_util.pydaw_read_file_text(f_full_path)
            if f_old == a_text:
                return None
            f_existed = 1
        else:
            f_old = ""
            f_existed = 0
        pydaw_util.pydaw_write_file_text(f_full_path, a_text)
        return f_existed, f_old

    def get_track_plugins(self, a_track_num):
        f_folder = self.track_pool_folder
        f_path = os.path.join(*(str(x) for x in (f_folder, a_track_num)))
        if os.path.isfile(f_path):
            with open(f_path) as f_handle:
                f_str = f_handle.read()
            return pydaw_track_plugins.from_str(f_str)
        else:
            return None

    def get_plugin_wav_pool_uids(self):
        result = set()
        for plugins in (
        self.get_track_plugins(x) for x in range(self.TRACK_COUNT)):
            if not plugins:
                continue
            for uid in plugins.get_wav_pool_uids():
                result.add(uid)
        return result


class AbstractTransport:
    pass


class pydaw_track_plugin:
    def __init__(self, a_index, a_plugin_index, a_plugin_uid,
                 a_mute=0, a_solo=0, a_power=1):
        self.index = int(a_index)  # index in the plugin chain
        self.plugin_index = int(a_plugin_index) # the plugin type
        self.plugin_uid = int(a_plugin_uid) # the uid in the project
        self.mute = int(a_mute)
        self.solo = int(a_solo)
        self.power = int(a_power)

    def get_wav_pool_uids(self):
        if not self.plugin_index:
            return set()
        plugin = mkplugins.PLUGIN_UI_TYPES[self.plugin_index]
        return plugin.get_wav_pool_uids(self.plugin_uid)

    def __str__(self):
        return "|".join(str(x) for x in
            ("p", self.index, self.plugin_index,
             self.plugin_uid, self.mute, self.solo, self.power))


class pydaw_track_plugins:
    def __init__(self):
        self.plugins = []

    def get_wav_pool_uids(self):
        result = set()
        for plugin in self.plugins:
            for uid in plugin.get_wav_pool_uids():
                result.add(uid)
        return result

    def __str__(self):
        return "\n".join(str(x) for x in self.plugins + ["\\"])

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_track_plugins()
        f_str = str(a_str)
        for f_line in f_str.split():
            if f_line == "\\":
                break
            f_line_arr = f_line.split("|")
            if f_line_arr[0] == "p":
                f_result.plugins.append(pydaw_track_plugin(*f_line_arr[1:]))
            else:
                assert(False)
        return f_result
