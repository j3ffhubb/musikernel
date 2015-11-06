# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import random
import os
import sys
import ctypes
import re
import subprocess
import time
import math
from math import log, pow
import multiprocessing
import numpy

try: #this will fail if imported by device dialog, but that's OK
    import mido
except ImportError:
    pass

from PyQt5 import QtCore
from PyQt5.QtWidgets import *


assert "cygwin" not in sys.platform, "Cygwin is unsupported"
IS_WINDOWS = "win32" in sys.platform or "msys" in sys.platform
IS_LINUX = "linux" in sys.platform
IS_MAC_OSX = "darwin" in sys.platform

IS_A_TTY = sys.stdin.isatty()

class WinVolInfo:
    def __init__(self):
        self.volumeNameBuffer = ctypes.create_unicode_buffer(1024)
        self.fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)

    def get_label(self, drive):
        #retcode = \
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            self.volumeNameBuffer,
            ctypes.sizeof(self.volumeNameBuffer),
            None, None, None,
            self.fileSystemNameBuffer,
            ctypes.sizeof(self.fileSystemNameBuffer)
        )
        return str(self.volumeNameBuffer.value)

if IS_WINDOWS:
    WIN_VOL_INFO = WinVolInfo()

def get_win_drives():
    from ctypes import windll
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for x in range(ord('A'), ord('Z') + 1):
        if bitmask & 1:
            drive = chr(x) + ":\\"
            label = WIN_VOL_INFO.get_label(drive)
            drives.append((drive, label))
        bitmask >>= 1
    return drives


PYTHON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MKENGINE_DIR = os.path.abspath(os.path.join(PYTHON_DIR, "..", "mkengine"))

pydaw_terminating_char = "\\"

global_pydaw_version_string = "musikernel2"
global_pydaw_file_type_string = 'MusiKernel Project (default.{})'.format(
    global_pydaw_version_string)
global_euphoria_file_type_string = 'Euphoria Sample File (*.u4ia4)'
global_euphoria_file_type_ext = '.u4ia4'

TIMESTRETCH_MODES = [
    "None", "Pitch(affecting time)", "Time(affecting pitch)",
    "Rubberband", "Rubberband(formants)", "SBSMS", "Paulstretch"]

TIMESTRETCH_INDEXES = {x:y for x, y in
    zip(TIMESTRETCH_MODES, range(len(TIMESTRETCH_MODES)))}

if IS_WINDOWS:
    TIMESTRETCH_MODES.remove("SBSMS")

CRISPNESS_SETTINGS = [
    "0 (smeared)", "1 (piano)", "2", "3",
    "4", "5 (normal)", "6 (sharp, drums)"]

BIN_PATH = None
RENDER_BIN_PATH = None
global_pydaw_is_sandboxed = False

global_pydaw_with_audio = True

CPU_COUNT = multiprocessing.cpu_count()
if CPU_COUNT < 1:
    CPU_COUNT = 1

if "src/pydaw/python/" in __file__:
    INSTALL_PREFIX = "/usr"
else:
    INSTALL_PREFIX = os.path.abspath(os.path.join(
        os.path.dirname(__file__), *([".."] * 5)))

BIN_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), *(([".."] * 5) + ["bin"])))

IS_ENGINE_LIB = False

ENGINE_LIB = None
ENGINE_LIB_THREAD = None
ENGINE_LIB_CALLBACK = None
ENGINE_LIB_CALLBACK_SIG = None

ICON_PATH = os.path.join(
    INSTALL_PREFIX, "share", "pixmaps",
    "{}.png".format(global_pydaw_version_string))

print("ICON_PATH = '{}'".format(ICON_PATH))

if IS_WINDOWS:
    DLL_EXT = ".dll"
    ICON_PATH = os.path.join(
        INSTALL_PREFIX, "{}.ico".format(global_pydaw_version_string))
elif IS_LINUX:
    DLL_EXT = ".so"
elif IS_MAC_OSX:
    DLL_EXT = ".dylib"

def load_engine_lib(a_engine_callback):
    global ENGINE_LIB, ENGINE_LIB_CALLBACK, ENGINE_LIB_CALLBACK_SIG
    f_dll_name = "{}{}".format(global_pydaw_version_string, DLL_EXT)
    f_dll = os.path.join(MKENGINE_DIR, f_dll_name)
    print("Using {}".format(f_dll))
    ENGINE_LIB = ctypes.CDLL(f_dll)
    ENGINE_LIB.main.restype = ctypes.c_int
    ENGINE_LIB.main.argstype = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
    ENGINE_LIB.v_configure.argstype = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    ENGINE_LIB.v_configure.restype = ctypes.c_int
    if IS_WINDOWS:
        ENGINE_LIB_CALLBACK_SIG = ctypes.WINFUNCTYPE(
            None, ctypes.c_char_p, ctypes.c_char_p)
    else:
        ENGINE_LIB_CALLBACK_SIG = ctypes.CFUNCTYPE(
            None, ctypes.c_char_p, ctypes.c_char_p)
    ENGINE_LIB_CALLBACK = ENGINE_LIB_CALLBACK_SIG(a_engine_callback)
    ENGINE_LIB.v_set_ui_callback.restype = None
    ENGINE_LIB.v_set_ui_callback(ENGINE_LIB_CALLBACK)

ENGINE_RETCODE = None

class EngineLibThread(QtCore.QThread):
    def run(self):
        global ENGINE_RETCODE
        myargv = ctypes.c_char_p * 5
        argv = myargv(
            "/usr/bin/{}-engine".format(
                global_pydaw_version_string).encode("ascii"),
            INSTALL_PREFIX.encode("ascii"),
            PROJECT_DIR.encode("ascii"), b"0",
            str(USE_HUGEPAGES).encode("ascii"))
        ENGINE_RETCODE = ENGINE_LIB.main(5, ctypes.byref(argv))
        print("ENGINE_RETCODE: {}".format(ENGINE_RETCODE))

def handle_engine_error(exitCode):
    if exitCode == 0:
        print("Engine exited with return code 0, no errors.")
        return

    import libmk

    if exitCode == 1000:
        QMessageBox.warning(
            libmk.MAIN_WINDOW, "Error", "Audio device not found")
    elif exitCode == 1001:
        QMessageBox.warning(
            libmk.MAIN_WINDOW, "Error", "Device config not found")
    elif exitCode == 1002:
        QMessageBox.warning(
            libmk.MAIN_WINDOW, "Error",
            "Unknown error opening audio device")
    if exitCode == 1003:
        QMessageBox.warning(
            libmk.MAIN_WINDOW, "Error",
            "The audio device was busy, make sure that no other applications "
            "are using the device and try restarting MusiKernel")
    else:
        QMessageBox.warning(
            libmk.MAIN_WINDOW, "Error",
            "The audio engine died with error code {}, "
            "please try restarting MusiKernel".format(exitCode))
    if exitCode >= 1000 and exitCode <= 1002:
        libmk.MAIN_WINDOW.on_change_audio_settings()


PROJECT_DIR = None

def run_musikernel():
    f_bin = pydaw_which(global_pydaw_version_string)
    subprocess.Popen([f_bin])

def start_engine_lib(a_project_dir):
    global PROJECT_DIR, ENGINE_LIB_THREAD
    PROJECT_DIR = a_project_dir
    ENGINE_LIB_THREAD = EngineLibThread()
    ENGINE_LIB_THREAD.start()

def engine_lib_configure(a_path, a_key, a_val):
    ENGINE_LIB.v_configure(
        a_path.encode("ascii"), a_key.encode("ascii"), a_val.encode("ascii"))


def pydaw_set_bin_path():
    global BIN_PATH, RENDER_BIN_PATH
    BIN_PATH = os.path.join(
        INSTALL_PREFIX, "bin",
        "{}-engine".format(global_pydaw_version_string))
    RENDER_BIN_PATH = os.path.join(
        INSTALL_PREFIX, "bin",
        "{}_render".format(global_pydaw_version_string))


def pydaw_escape_stylesheet(a_stylesheet, a_path):
    f_dir = os.path.dirname(str(a_path))
    if IS_WINDOWS:
        f_dir = f_dir[0].lower() + f_dir[1:].replace("\\", "/")
    f_result = a_stylesheet.replace("$STYLE_FOLDER", f_dir)
    return f_result

def check_for_rw_perms(a_parent, a_file):
    if not os.access(os.path.dirname(str(a_file)), os.W_OK):
        QMessageBox.warning(
            a_parent, "Error",
            "You do not have read+write permissions to "
            "{}".format(global_pydaw_home))
        return False
    else:
        return True

def check_for_empty_directory(a_parent, a_dir):
    """ Return true if directory is empty, show error message and
        return False if not
    """
    if os.listdir(a_dir):
        QMessageBox.warning(a_parent, "Error",
        "You must save the project file to an empty directory, use "
        "the 'Create Folder' button to create a new, empty directory.")
        return False
    else:
        return True

def new_project(a_parent=None):
    try:
        f_last_dir = global_pydaw_home
        while True:
            f_file = QFileDialog.getExistingDirectory(
                a_parent, 'New Project', f_last_dir,
                QFileDialog.ShowDirsOnly)
            if f_file and str(f_file):
                f_file = str(f_file)
                f_last_dir = f_file
                if not check_for_empty_directory(a_parent, f_file) or \
                not check_for_rw_perms(a_parent, f_file):
                    continue
                f_file += "/default." + global_pydaw_version_string
                set_file_setting("last-project", f_file)
                return True
            else:
                return False
    except Exception as ex:
        QMessageBox.warning(a_parent, "Error", str(ex))

def open_project(a_parent=None):
    try:
        f_file, f_filter = QFileDialog.getOpenFileName(
            parent=a_parent, caption='Open Project',
            directory=global_default_project_folder,
            filter=global_pydaw_file_type_string)
        if f_file is None:
            return False
        f_file_str = str(f_file)
        if not f_file_str:
            return False
        if not check_for_rw_perms(a_parent, f_file):
            return False
        #global_open_project(f_file_str)
        set_file_setting("last-project", f_file_str)
        return True
    except Exception as ex:
        QMessageBox.warning(a_parent, "Error", str(ex))

print("\n\n\ninstall prefix:  {}\n\n\n".format(INSTALL_PREFIX))

PROJECT_HISTORY_SCRIPT = os.path.join(
    INSTALL_PREFIX, "lib", global_pydaw_version_string,
    "pydaw", "python", "libpydaw", "project_recover.py")

pydaw_bad_chars = ["|", "\\", "~", "."]

def pi_path(a_file):
    "Platform independent path"
    a_file = os.path.normpath(str(a_file))
    return a_file.replace("\\", "/") if IS_WINDOWS else a_file


def pydaw_which(a_file):
    """ Python equivalent of the UNIX "which" command """
    f_path_arr = os.getenv("PATH").split(";" if IS_WINDOWS else ":")
    if IS_WINDOWS and BIN_DIR not in f_path_arr:
        f_path_arr.insert(0, BIN_DIR)
    for f_path in (pi_path(x) for x in f_path_arr):
        f_file_path = os.path.join(f_path, a_file)
        if os.path.exists(f_file_path) and not os.path.isdir(f_file_path):
            return f_file_path
        if IS_WINDOWS:
            f_file_path += ".exe"
            if os.path.exists(f_file_path) \
            and not os.path.isdir(f_file_path):
                return f_file_path
    return None


def get_unix_timestamp(a_dt):
    if IS_WINDOWS:
        assert sys.version_info >= (3, 3), "Must have Python3.3 or later"
        return int(a_dt.timestamp())
    else:
        return int(a_dt.strftime("%s"))


def pydaw_remove_bad_chars(a_str):
    """ Remove any characters that have special meaning to MusiKernel """
    f_str = str(a_str)
    for f_char in pydaw_bad_chars:
        f_str = f_str.replace(f_char, "")
    return f_str


def pydaw_str_has_bad_chars(a_str):
    f_str = str(a_str)
    for f_char in pydaw_bad_chars:
        if f_char in f_str:
            return False
    return True


def case_insensitive_path(a_path, a_assert=True):
    f_path = os.path.abspath(str(a_path))
    if os.path.exists(f_path):
        return a_path
    else:
        if os.path.sep != '/' and os.path.sep in f_path:
            f_path_arr = f_path.split(os.path.sep)
        else:
            f_path_arr = f_path.split('/')
        f_path_arr = [x for x in f_path_arr if x]
        f_path = "" if IS_WINDOWS else "/"
        for f_dir in f_path_arr:
            if os.path.exists(os.path.join(f_path, f_dir)):
                f_path = os.path.join(f_path, f_dir)
            else:
                f_found = False
                for f_real_dir in os.listdir(f_path):
                    if f_dir.lower() == f_real_dir.lower():
                        f_found = True
                        f_path = os.path.join(f_path, f_real_dir)
                        break
                if not f_found:
                    if a_assert:
                        assert False, "File not found '{}'".format(a_path)
                    else:
                        return None
        print(f_path)
        return f_path

def count_beats(a_start_bar, a_start_beat, a_end_bar, a_end_beat):
    a_start_bar, a_end_bar = (int(x) for x in (a_start_bar, a_end_bar))
    a_start_beat, a_end_beat = (float(x) for x in (a_start_beat, a_end_beat))
    return ((a_end_bar - a_start_bar) * 4.0) + (a_end_beat - a_start_beat)


AUDIO_FILE_EXTS = [".WAV", ".AIF", ".AIFF", ".FLAC"]
MIDI_FILE_EXTS = [".MIDI", ".MID"]
AUDIO_MIDI_FILE_EXTS = AUDIO_FILE_EXTS + MIDI_FILE_EXTS

MAX_EXT_LEN = max(len(x) for x in AUDIO_MIDI_FILE_EXTS)

def is_audio_file(a_file):
    return is_file_type(a_file, AUDIO_FILE_EXTS)

def is_midi_file(a_file):
    return is_file_type(a_file, MIDI_FILE_EXTS)

def is_audio_midi_file(a_file):
    return is_file_type(a_file, AUDIO_MIDI_FILE_EXTS)

def is_file_type(a_file, a_list):
    """ Only checks the extension, not the MIME type """
    f_file = str(a_file)[-MAX_EXT_LEN:].upper()
    for f_file in (x for x in a_list if f_file.endswith(x)):
        return True
    return False

beat_fracs = ['1/16', '1/8', '1/4', '1/3', '1/2', '1/1']

def beat_frac_text_to_float(f_index):
    if f_index == 0:
        return 0.0625
    elif f_index == 1:
        return 0.125
    elif f_index == 2:
        return 0.25
    elif f_index == 3:
        return 0.33333333
    elif f_index == 4:
        return 0.5
    elif f_index == 5:
        return 1.0
    else:
        return 0.25

bar_fracs = ['1/4', '1/8', '1/12', '1/16', '1/32']

bar_fracs_dict = {'1/4':0.25, '1/8':0.125, '1/12':0.083333333,
                  '1/16':0.0625, '1/32':0.03125}

def bar_frac_text_to_float(a_text):
    return bar_fracs_dict[str(a_text)] * 4.0

def scale_to_rect(a_to_scale, a_scale_to):
    """ Returns a tuple that scales one QRectF to another """
    f_x = (a_scale_to.width() / a_to_scale.width())
    f_y = (a_scale_to.height() / a_to_scale.height())
    return (f_x, f_y)

def scale_sizes(a_width_from, a_height_from, a_width_to, a_height_to):
    f_x = a_width_to / a_width_from
    f_y = a_height_to / a_height_from
    return (f_x, f_y)


def pydaw_beats_to_index(a_beat, a_divisor=4.0):
    f_index = int(a_beat / a_divisor)
    f_start = a_beat - (float(f_index) * a_divisor)
    return f_index, round(f_start, 6)

int_to_note_array = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#',
                     'G', 'G#', 'A', 'A#', 'B']

TERMINAL = None

for _terminal in ("x-terminal-emulator", "gnome-terminal", "konsole"):
    if pydaw_which(_terminal):
        TERMINAL = _terminal
        break

PYTHON3 = sys.executable

pydaw_rubberband_util = pydaw_which("rubberband")

pydaw_paulstretch_util = os.path.join(
    INSTALL_PREFIX, "lib", global_pydaw_version_string,
    "pydaw", "python", "libpydaw", "pydaw_paulstretch.py")

if IS_WINDOWS:
    pydaw_sbsms_util = os.path.join(
        INSTALL_PREFIX, "python", "mkengine", "sbsms.exe")
else:
    pydaw_sbsms_util = os.path.join(
        INSTALL_PREFIX, "lib", global_pydaw_version_string,
        "sbsms", "bin", "sbsms")


def pydaw_rubberband(a_src_path, a_dest_path, a_timestretch_amt, a_pitch_shift,
                     a_crispness, a_preserve_formants=False):
    if a_preserve_formants:
        f_cmd = [pydaw_rubberband_util, "-F", "-c", str(a_crispness), "-t",
             str(a_timestretch_amt), "-p", str(a_pitch_shift),
             "-R", "--pitch-hq", a_src_path, a_dest_path]
    else:
        f_cmd = [pydaw_rubberband_util, "-c", str(a_crispness), "-t",
             str(a_timestretch_amt), "-p", str(a_pitch_shift),
             "-R", "--pitch-hq", a_src_path, a_dest_path]
    print("Running {}".format(" ".join(f_cmd)))
    f_proc = subprocess.Popen(f_cmd)
    return f_proc

def pydaw_sbsms(a_src_path, a_dest_path, a_timestretch_amt, a_pitch_shift):
    f_cmd = [pydaw_sbsms_util, a_src_path, a_dest_path,
             str(1.0 / a_timestretch_amt), str(1.0 / a_timestretch_amt),
             str(a_pitch_shift), str(a_pitch_shift) ]
    print("Running {}".format(" ".join(f_cmd)))
    f_proc = subprocess.Popen(f_cmd)
    return f_proc

def pydaw_clip_value(a_val, a_min, a_max, a_round=False):
    if a_val < a_min:
        f_result = a_min
    elif a_val > a_max:
        f_result =  a_max
    else:
        f_result = a_val
    if a_round:
        f_result = round(f_result, 6)
    return f_result

def pydaw_clip_min(a_val, a_min):
    if a_val < a_min:
        return a_min
    else:
        return a_val

def pydaw_clip_max(a_val, a_max):
    if a_val > a_max:
        return a_max
    else:
        return a_val

def pydaw_read_file_text(a_file):
    with open(pi_path(a_file)) as f_handle:
        return f_handle.read()

def pydaw_write_file_text(a_file, a_text):
    with open(pi_path(a_file), "w", newline="\n") as f_handle:
        f_handle.write(str(a_text))

def pydaw_gen_uid():
    """Generated an integer uid.  Adding together multiple random
        numbers gives a far less uniform distribution of
        numbers, more of a natural white noise kind of sample graph
        than a brick-wall digital white noise... """
    f_result = 5
    for i in range(6):
        f_result += random.randint(6, 50000000)
    return f_result

def note_num_to_string(a_note_num):
    f_note = int(a_note_num) % 12
    f_octave = (int(a_note_num) // 12) - 2
    return "{}{}".format(int_to_note_array[f_note], f_octave)

def string_to_note_num(a_str):
    f_str = str(a_str).lower()
    if len(f_str) >=2 and len(f_str) < 5 and re.match('[a-g](.*)[0-8]', f_str):
        f_notes = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11}
        for k, v in f_notes.items():
            if f_str.startswith(k):
                f_str = f_str.replace(k, "", 1)
                f_sharp_flat = 0
                if f_str.startswith("#"):
                    f_sharp_flat = 1
                    f_str = f_str[1:]
                elif f_str.startswith("b"):
                    f_sharp_flat = -1
                    f_str = f_str[1:]
                f_result = (int(f_str) * 12) + v + f_sharp_flat
                assert(f_result >= 0 and f_result <= 127)
                return f_result
        return a_str
    else:
        return a_str

def bool_to_int(a_bool):
    if a_bool:
        return "1"
    else:
        return "0"

def int_to_bool(a_int):
    if isinstance(a_int, bool):
        return a_int

    if int(a_int) == 0:
        return False
    elif int(a_int) == 1:
        return True
    else:
        assert(False)

class MidiEvent:
    def __init__(self, a_ev, a_start_beat):
        self.ev = a_ev
        self.start_beat = a_start_beat
        self.type = a_ev.type

    def __lt__(self, other):
        return self.start_beat < other.start_beat

def load_midi_file(a_file):
    f_midi_text_arr = mido.MidiFile(str(a_file))
    #First fix the lengths of events that have note-off events
    f_note_on_dict = {}
    f_item_list = []
    f_pos = 0
    f_sec_per_beat = 0.5
    for f_ev in f_midi_text_arr:
        if f_ev.type == "set_tempo":
            f_sec_per_beat = f_ev.tempo / 1000000.0
        elif f_ev.type == "note_off" or (
        f_ev.type == "note_on" and f_ev.velocity == 0):
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_event = f_note_on_dict[f_tuple]
                f_event.length = f_pos - f_event.start_beat
                f_item_list.append(f_event)
                f_note_on_dict.pop(f_tuple)
            else:
                print("Error, note-off event does not correspond to a "
                      "note-on event, ignoring event:\n{}".format(f_ev))
        elif f_ev.type == "note_on":
            f_event = MidiEvent(f_ev, f_pos)
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_note_on_dict[f_tuple].length = f_pos - f_event.start_beat
            f_note_on_dict[f_tuple] = f_event
        else:
            print("Ignoring event: {}".format(f_ev))
        f_pos += f_ev.time / f_sec_per_beat

    f_item_list.sort()
    return f_item_list

def print_sorted_dict(a_dict):
    """ Mostly intended for printing locals() and globals() """
    for k in sorted(list(a_dict.keys())):
        print("{} : {}".format(k, a_dict[k]))

def time_quantize_round(a_input):
    """Properly quantize time values from QDoubleSpinBoxes
        that measure beats
    """
    if round(a_input) == round(a_input, 2):
        return round(a_input)
    else:
        return round(a_input, 6)

def pydaw_pitch_to_hz(a_pitch):
    return (440.0 * pow(2.0, (float(a_pitch) - 57.0) * 0.0833333))

def pydaw_hz_to_pitch(a_hz):
    return ((12.0 * log(float(a_hz) * (1.0 / 440.0), 2.0)) + 57.0)

def pydaw_pitch_to_ratio(a_pitch):
    return (1.0 / pydaw_pitch_to_hz(0.0)) * pydaw_pitch_to_hz(float(a_pitch))

def pydaw_ratio_to_pitch(a_ratio):
    f_base = (pydaw_pitch_to_hz(0.0))
    f_hz = f_base * a_ratio
    return pydaw_hz_to_pitch(f_hz)

def pydaw_db_to_lin(a_value):
    return pow(10.0, (0.05 * float(a_value)))

def pydaw_lin_to_db(a_value):
    if a_value >= 0.001:
        return log(float(a_value), 10.0) * 20.0
    else:
        return -120.0

def musical_time_to_seconds(a_tempo, a_bar, a_beat):
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_beats = (float(a_bar) * 4.0) + float(a_beat)
    return f_seconds_per_beat * f_beats

def seconds_to_beats(a_tempo, a_seconds):
    f_seconds_per_beat = 60.0 / float(a_tempo)
    return float(a_seconds) / f_seconds_per_beat

def linear_interpolate(a_point1, a_point2, a_frac):
    return ((a_point2 - a_point1) * a_frac) + a_point1

def cosine_interpolate(y1, y2, mu):
   mu2 = (1.0 - math.cos(mu * math.pi)) / 2
   return(y1 * (1.0 - mu2) + y2 * mu2)


class OnePoleLP:
    def __init__(self, a_val, a_fc=0.33):
        self.a0 = 1.0
        self.b1 = 0.0
        self.z1 = a_val
        self.set_fc(a_fc)

    def set_fc(self, a_fc):
        self.b1 = math.exp(-2.0 * math.pi * a_fc);
        self.a0 = 1.0 - self.b1;

    def process(self, a_in):
        self.z1 = a_in * self.a0 + self.z1 * self.b1
        return self.z1


def cubic_interpolate(a_arr, a_pos):
    f_int_pos = pydaw_clip_value(int(a_pos), 0, a_arr.shape[0] - 1)
    f_mu = a_pos - float(f_int_pos)
    f_mu2 = f_mu * f_mu
    f_int_pos_plus1 = pydaw_clip_value(f_int_pos + 1, 0, a_arr.shape[0] - 1)
    f_int_pos_minus1 = pydaw_clip_value(f_int_pos - 1, 0, a_arr.shape[0] - 1)
    f_int_pos_minus2 = pydaw_clip_value(f_int_pos - 2, 0, a_arr.shape[0] - 1)

    f_a0 = (a_arr[f_int_pos_plus1] - a_arr[f_int_pos] -
        a_arr[f_int_pos_minus2] + a_arr[f_int_pos_minus1])
    f_a1 = a_arr[f_int_pos_minus2] - a_arr[f_int_pos_minus1] - f_a0
    f_a2 = a_arr[f_int_pos] - a_arr[f_int_pos_minus2]
    f_a3 = a_arr[f_int_pos_minus1]

    return (f_a0 * f_mu * f_mu2 + f_a1 * f_mu2 + f_a2 * f_mu + f_a3)

def np_linear_interpolate(a_array, a_pos):
    f_int = int(a_pos)
    f_frac = a_pos - f_int
    try:
        f_point1 = a_array[f_int]
        f_point2 = a_array[f_int + 1]
    except IndexError:
        return a_array[-1]
    return ((f_point2 - f_point1) * f_frac) + f_point1

def np_resample(a_array, a_new_size):
    a_new_size = int(a_new_size) + 1
    f_result = numpy.zeros(a_new_size)
    f_len = a_array.shape[0]
    f_stride = float(f_len) / a_new_size
    f_pos = 0.0
    for f_i in range(a_new_size):
        f_result[f_i] = np_linear_interpolate(a_array, f_pos)
        f_pos += f_stride
    return f_result

def window_rms(a_arr, a_window_size):
  a2 = numpy.power(a_arr, 2)
  window = numpy.ones(a_window_size) / float(a_window_size)
  return numpy.sqrt(numpy.convolve(a2, window, 'valid'))

def rate_env(a_audio_item, a_src_path, a_dest_path):
    f_rate_diff = float(a_audio_item.timestretch_amt_end -
        a_audio_item.timestretch_amt)
    f_start_rate = a_audio_item.timestretch_amt

    with wavefile.WaveReader(a_src_path) as f_reader:
        with wavefile.WaveWriter(
        a_dest_path, channels=f_reader.channels) as f_writer:
            f_shape = (f_reader.channels, f_reader.frames)
            f_arr = numpy.zeros(f_shape, numpy.float32, order='F')
            f_reader.read(f_arr)
            f_block_size = 100000
            f_output = numpy.zeros((f_reader.channels, f_block_size))
            f_sample_pos = 0.0
            while int(f_sample_pos) < f_reader.frames:
                f_size = 0
                while f_size < f_block_size:
                    for f_ch in range(f_arr.shape[0]):
                        f_output[f_ch][f_size] = cubic_interpolate(
                            f_arr[f_ch], f_sample_pos)
                    f_size += 1
                    f_rate = (f_rate_diff * (f_sample_pos /
                        float(f_reader.frames))) + f_start_rate
                    f_sample_pos += f_rate
                    if int(f_sample_pos) >= f_reader.frames:
                        break
                if f_size >= f_block_size:
                    f_writer.write(f_output)
                else:
                    f_writer.write(f_output[:,:f_size])

def pydaw_wait_for_finished_file(a_file):
    """ Wait until a_file exists, then delete it and return.  It should
    already have the .finished extension"""
    while True:
        if os.path.isfile(a_file):
            try:
                os.remove(a_file)
                break
            except:
                print("pydaw_wait_for_finished_file:  Exception "
                    "when deleting {}".format(a_file))
        else:
            time.sleep(0.1)

def pydaw_get_wait_file_path(a_file):
    f_wait_file = "{}.finished".format(a_file)
    if os.path.isfile(f_wait_file):
        os.remove(f_wait_file)
    return f_wait_file

def pydaw_seconds_to_time_str(a_seconds, a_sections=1):
    f_seconds = float(a_seconds)
    f_inc = f_seconds / a_sections
    if f_seconds > 3600.0:  # 60 * 60
        if a_sections == 1:
            return time.strftime("%H:%M", time.gmtime(f_seconds))
        else:
            return [time.strftime("%H:%M", time.gmtime(x * f_inc))
                for x in range(a_sections)]
    elif f_seconds > 60.0:
        if a_sections == 1:
            return time.strftime("%M:%S", time.gmtime(f_seconds))
        else:
            return [time.strftime("%M:%S", time.gmtime(x * f_inc))
                for x in range(a_sections)]
    else:
        if a_sections == 1:
            return str(round(f_seconds, 2))
        else:
            return [str(round(x * f_inc, 2)) for x in range(a_sections)]


global_show_create_folder_error = False

global_is_live_mode = False
global_home = os.path.expanduser("~")

global_pydaw_home = os.path.join(global_home, global_pydaw_version_string)
global_default_project_folder = global_pydaw_home

CONFIG_DIR = os.path.join(global_pydaw_home, "config")
PRESET_DIR = os.path.join(CONFIG_DIR, "preset")

for _f_dir in (global_pydaw_home, CONFIG_DIR, PRESET_DIR):
    if not os.path.isdir(_f_dir):
        os.makedirs(_f_dir)


def get_file_setting(a_name, a_type, a_default):
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    if os.path.exists(f_file_name):
        try:
            with open(f_file_name) as f_file:
                return a_type(f_file.read())
        except Exception as ex:
            print("Error in get_file_setting {}".format(ex))
            os.remove(f_file_name)
    return a_default

def set_file_setting(a_name, a_val):
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    with open(f_file_name, "w", newline="\n") as f_file:
        f_file.write(str(a_val))

USE_HUGEPAGES = 0

global_device_val_dict = {}
global_pydaw_device_config = os.path.join(CONFIG_DIR, "device.txt")

MIDI_IN_DEVICES = []

SAMPLE_RATE = None
NYQUIST_FREQ = None

def pydaw_delete_device_config():
    global global_device_val_dict
    global_device_val_dict = {}
    if os.path.exists(global_pydaw_device_config):
        os.remove(global_pydaw_device_config)

def pydaw_read_device_config():
    global BIN_PATH, global_device_val_dict, MIDI_IN_DEVICES, IS_ENGINE_LIB
    global global_pydaw_is_sandboxed, global_pydaw_with_audio, USE_HUGEPAGES

    global_device_val_dict = {}
    MIDI_IN_DEVICES = []

    try:
        if os.path.isfile(global_pydaw_device_config):
            f_file_text = pydaw_read_file_text(global_pydaw_device_config)
            for f_line in f_file_text.split("\n"):
                if f_line.strip() == "\\":
                    break
                if f_line.strip() != "":
                    f_key, f_val = (x.strip() for x in f_line.split("|", 1))
                    if f_key == "midiInDevice":
                        MIDI_IN_DEVICES.append(f_val)
                    else:
                        global_device_val_dict[f_key] = f_val
            MIDI_IN_DEVICES.sort()
            pydaw_set_bin_path()
            global_pydaw_is_sandboxed = False
            global_pydaw_with_audio = True

            if "hugePages" in global_device_val_dict and \
            int(global_device_val_dict["hugePages"]) == 1:
                USE_HUGEPAGES = 1

            f_selinux = False
            if IS_LINUX:
                try:
                    if pydaw_which("getenforce") and subprocess.check_output(
                    "getenforce").strip().lower() == b"enforcing":
                        f_selinux = True
                except Exception as ex:
                    print("Exception while checking getenforce, "
                        "assuming SELinux is enabled\n{}".format(ex))
                    f_selinux = True

                if f_selinux:
                    print("SELinux detected, not using any setuid "
                        "binaries to prevent lockups.")

            if not IS_LINUX:
                BIN_PATH = None
                global_device_val_dict["audioEngine"] = 8
                IS_ENGINE_LIB = True

            if BIN_PATH is not None:
                if int(global_device_val_dict["audioEngine"]) == 0:
                    BIN_PATH += "-no-root"
                elif int(global_device_val_dict["audioEngine"]) <= 2:
                    # The setuid binaries will get blocked by
                    # SELinux, so don't use
                    if f_selinux:
                        BIN_PATH += "-no-root"
                    elif int(global_device_val_dict["audioEngine"]) == 2:
                        BIN_PATH = os.path.join(
                            INSTALL_PREFIX, "bin",
                            global_pydaw_version_string)
                        global_pydaw_is_sandboxed = True
                elif int(global_device_val_dict["audioEngine"]) == 3 or \
                int(global_device_val_dict["audioEngine"]) == 4 or \
                int(global_device_val_dict["audioEngine"]) == 5 or \
                int(global_device_val_dict["audioEngine"]) == 7:
                    BIN_PATH += "-dbg"
                elif int(global_device_val_dict["audioEngine"]) == 6:
                    global_pydaw_with_audio = False
                    BIN_PATH = None
                elif int(global_device_val_dict["audioEngine"]) == 8:
                    IS_ENGINE_LIB = True
            global SAMPLE_RATE, NYQUIST_FREQ
            SAMPLE_RATE = int(global_device_val_dict["sampleRate"])
            NYQUIST_FREQ = SAMPLE_RATE / 2
    except Exception as ex:
        print("Exception while reading device config,"
            " deleting and starting over\n{}".format(ex))
        global_device_val_dict = {}

    print("BIN_PATH == {}".format(BIN_PATH))

pydaw_read_device_config()

BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "file_browser_bookmarks.txt")

def global_get_file_bookmarks():
    try:
        f_result = {}
        if os.path.isfile(BOOKMARKS_FILE):
            f_text = pydaw_read_file_text(BOOKMARKS_FILE)
            f_arr = f_text.split("\n")
            for f_line in f_arr:
                f_line_arr = f_line.split("|||", 2)
                if len(f_line_arr) != 3:
                    break
                if os.path.isdir(f_line_arr[2]):
                    if not f_line_arr[1] in f_result:
                        f_result[f_line_arr[1]] = {}
                    f_result[f_line_arr[1]][f_line_arr[0]] = f_line_arr[2]
                else:
                    print("Warning:  Not loading bookmark '{}' "
                        "because the directory '{}' does not "
                        "exist.".format(f_line_arr[0], f_line_arr[2]))
        return f_result
    except Exception as ex:
        print("Error getting bookmarks:\n".format(ex))
        return {}

def global_write_file_bookmarks(a_dict):
    f_result = []
    for k in sorted(a_dict.keys()):
        v = a_dict[k]
        for k2 in sorted(v.keys()):
            v2 = v[k2]
            f_result.append("{}|||{}|||{}".format(k2, k, v2))
    pydaw_write_file_text(BOOKMARKS_FILE, "\n".join(f_result))

def global_add_file_bookmark(a_name, a_folder, a_category):
    f_dict = global_get_file_bookmarks()
    f_category = str(a_category)
    if not f_category in f_dict:
        f_dict[f_category] = {}
    f_dict[f_category][str(a_name)] = str(a_folder)
    global_write_file_bookmarks(f_dict)

def global_delete_file_bookmark(a_category, a_name):
    f_dict = global_get_file_bookmarks()
    f_key = str(a_category)
    f_name = str(a_name)
    if f_key in f_dict:
        if f_name in f_dict[f_key]:
            f_dict[f_key].pop(f_name)
            global_write_file_bookmarks(f_dict)
        else:
            print("{} was not in the bookmarks file, it may "
                "have been deleted in a different "
                "file browser widget".format(f_key))

class sfz_exception(Exception):
    pass

class sfz_sample:
    """ Corresponds to the settings for a single sample """
    def __init__(self):
        self.dict = {}

    def set_from_group(self, a_group_list):
        """ a_group_list: should be in order of least precedence to
        most precedence, ie:  values in the last group can overwrite
        values set by the first group."""
        for f_group in filter(None, a_group_list):
            for k, v in f_group.dict.items():
                if k not in self.dict or v is not None:
                    self.dict[k] = v

    def __str__(self):
        return str(self.dict)


class sfz_file:
    """ Abstracts an .sfz file into a list of sfz_sample whose dicts
    correspond to the attributes of a single sample."""
    def __init__(self, a_file_path):
        self.path = str(a_file_path)
        if not os.path.exists(self.path):
            raise sfz_exception("{} does not exist.".format(self.path))
        f_file_text = pydaw_read_file_text(self.path)
        # In the wild, people can and often do put tags and opcodes on the same
        # line, move all tags and opcodes to their own line
        f_file_text = f_file_text.replace("<", "\n<")
        f_file_text = f_file_text.replace(">", ">\n")
        f_file_text = f_file_text.replace("/*", "\n/*")
        f_file_text = f_file_text.replace("*/", "*/\n")
        f_file_text = f_file_text.replace("\t", " ")
        f_file_text = f_file_text.replace("\r", "")

        f_file_text_new = ""

        for f_line in f_file_text.split("\n"):
            if f_line.strip().startswith("//"):
                continue
            if "=" in f_line:
                f_line_arr = f_line.split("=")
                for f_i in range(1, len(f_line_arr)):
                    f_opcode = f_line_arr[f_i - 1].strip().rsplit(" ")[-1]
                    if f_i == (len(f_line_arr) - 1):
                        f_value = f_line_arr[f_i]
                    else:
                        f_value = f_line_arr[f_i].strip().rsplit(" ", 1)[0]
                    f_file_text_new += "\n{}={}\n".format(f_opcode, f_value)
            else:
                f_file_text_new += "{}\n".format(f_line)

        f_file_text = f_file_text_new
        self.adjusted_file_text = f_file_text_new

        f_global_settings = None
        f_current_group = None
        f_current_region = None
        f_current_object = None

        f_extended_comment = False

        self.samples = []
        f_samples_list = []

        #None = unsupported, 0 = global, 1 = region, 2 = group
        f_current_mode = None

        for f_line in f_file_text.split("\n"):
            f_line = f_line.strip()

            if f_line.startswith("/*"):
                f_extended_comment = True
                continue

            if f_extended_comment:
                if "*/" in f_line:
                    f_extended_comment = False
                continue

            if f_line == "" or f_line.startswith("//"):
                continue
            if re.match("<(.*)>", f_line) is not None:
                if f_line.startswith("<global>"):
                    f_current_mode = 0
                    f_global_settings = sfz_sample()
                    f_current_object = f_global_settings
                elif f_line.startswith("<region>"):
                    f_current_mode = 1
                    f_current_region = sfz_sample()
                    f_current_object = f_current_region
                    f_samples_list.append(f_current_region)
                elif f_line.startswith("<group>"):
                    f_current_mode = 2
                    f_current_group = sfz_sample()
                    f_current_object = f_current_group
                else:
                    f_current_mode = None
            else:
                if f_current_mode is None:
                    continue
                try:
                    f_key, f_value = f_line.split("=")
                    f_value = string_to_note_num(f_value)
                except Exception as ex:
                    print("ERROR:  {}".format(f_line))
                    raise sfz_exception(
                        "Error parsing key/value pair\n{}\n{}".format(
                        f_line, ex))
                if f_key.lower() == "sample" and \
                not is_audio_file(f_value.strip()):
                    raise sfz_exception(
                        "{} not supported, only {} supported.".format(
                        f_value, AUDIO_FILE_EXTS))
                f_current_object.dict[f_key.lower()] = f_value
                if f_current_mode == 1:
                    f_current_object.set_from_group(
                        [f_global_settings, f_current_group])

        for f_region in f_samples_list:
            if "sample" in f_region.dict:
                self.samples.append(f_region)

    def __str__(self):
        #return self.adjusted_file_text
        f_result = ""
        for f_sample in self.samples:
            f_result += "\n\n{}\n\n".format(f_sample)
        return f_result


DEFAULT_STYLESHEET_FILE = os.path.join(
    INSTALL_PREFIX, "lib", global_pydaw_version_string,
    "themes", "default", "default.pytheme")

STYLESHEET_FILE = get_file_setting("default-style", str, None)

if not (STYLESHEET_FILE and os.path.isfile(STYLESHEET_FILE)):
    STYLESHEET_FILE = DEFAULT_STYLESHEET_FILE

print("Using stylesheet " + STYLESHEET_FILE)
global_stylesheet = pydaw_read_file_text(STYLESHEET_FILE)
global_stylesheet = pydaw_escape_stylesheet(global_stylesheet, STYLESHEET_FILE)
global_stylesheet_dir = os.path.dirname(STYLESHEET_FILE)


def pydaw_rgb_minus(a_rgb, a_amt):
    f_result = []
    for f_color in a_rgb:
        f_result.append(pydaw_clip_min(f_color - a_amt, 0))
    return f_result

def pydaw_rgb_plus(a_rgb, a_amt):
    f_result = []
    for f_color in a_rgb:
        f_result.append(pydaw_clip_max(f_color + a_amt, 255))
    return f_result

class pydaw_name_uid_dict:
    def gen_file_name_uid(self):
        while self.high_uid in self.name_lookup:
            self.high_uid += 1
        return self.high_uid

    def __init__(self):
        self.high_uid = 0
        self.name_lookup = {}
        self.uid_lookup = {}

    def add_item(self, a_uid, a_name):
        f_uid = int(a_uid)
        a_name = pi_path(a_name)
        self.name_lookup[f_uid] = a_name
        self.uid_lookup[a_name] = f_uid
        if f_uid > self.high_uid:
            self.high_uid = f_uid

    def add_new_item(self, a_name, a_uid=None):
        if a_name in self.uid_lookup:
            raise Exception
        if a_uid is None:
            f_uid = self.gen_file_name_uid()
        else:
            f_uid = a_uid
        self.add_item(f_uid, a_name)
        return f_uid

    def get_uid_by_name(self, a_name):
        return self.uid_lookup[str(a_name)]

    def get_name_by_uid(self, a_uid):
        return self.name_lookup[int(a_uid)]

    def rename_item(self, a_old_name, a_new_name):
        f_uid = self.get_uid_by_name(a_old_name)
        f_new_name = str(a_new_name)
        f_old_name = self.name_lookup[f_uid]
        self.uid_lookup.pop(f_old_name)
        self.add_item(f_uid, f_new_name)

    def uid_exists(self, a_uid):
        return int(a_uid) in self.name_lookup

    def name_exists(self, a_name):
        return str(a_name) in self.uid_lookup

    def get_takes(self):
        f_result = {}
        for k in self.uid_lookup:
            f_regex = re.search("[0-9]+$", k)
            if f_regex:
                f_int = f_regex.group()
                f_str = k[:f_regex.start()]
                if f_str in f_result:
                    f_result[f_str].append(f_int)
                else:
                    f_result[f_str] = [f_int]
        return {k:sorted(v, key=lambda x: int(x))
            for k, v in f_result.items() if len(v) > 1}

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_name_uid_dict()
        f_lines = a_str.split("\n")
        for f_line in f_lines:
            if f_line == pydaw_terminating_char:
                break
            f_arr = f_line.split("|", 1)
            f_uid = int(f_arr[0])
            f_name = f_arr[1]
            f_result.add_item(f_uid, f_name)
        return f_result

    def __str__(self):
        f_result = []
        for k in sorted(self.name_lookup.keys()):
            v = self.name_lookup[k]
            f_result.append("|".join((str(k), pi_path(v))))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    def __len__(self):
        return len(self.name_lookup)

def proj_file_str(a_val):
    f_val = a_val
    if isinstance(f_val, float):
        f_val = round(a_val, 6)
    return str(f_val)

