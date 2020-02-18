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

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from libpydaw import *
from libpydaw.pydaw_util import *
import libmk
import collections
import shutil
import tarfile
import json
import datetime
import os
import numpy

pydaw_folder_audio = os.path.join("audio", "files")
pydaw_folder_audio_rec = os.path.join("audio", "rec")
pydaw_folder_samplegraph = os.path.join("audio", "samplegraph")
pydaw_folder_samples = os.path.join("audio", "samples")
pydaw_folder_timestretch = os.path.join("audio", "timestretch")
pydaw_folder_glued = os.path.join("audio", "glued")
pydaw_folder_user = "user"
pydaw_folder_backups = "backups"
pydaw_folder_projects = "projects"
pydaw_folder_plugins = os.path.join("projects", "plugins")
pydaw_file_plugin_uid = os.path.join("projects", "plugin_uid.txt")
pydaw_file_pywavs = os.path.join("audio", "wavs.txt")
pydaw_file_pystretch = os.path.join("audio", "stretch.txt")
pydaw_file_pystretch_map = os.path.join("audio", "stretch_map.txt")
pydaw_file_backups = "backups.json"


class MkProject(libmk.AbstractProject):
    def __init__(self):
        self.cached_audio_files = []
        self.glued_name_index = 0

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]

        self.audio_folder = os.path.join(
            self.project_folder, pydaw_folder_audio)
        self.audio_rec_folder = os.path.join(
            self.project_folder, pydaw_folder_audio_rec)
        self.audio_tmp_folder = os.path.join(
            self.project_folder, pydaw_folder_audio, "tmp")
        self.samplegraph_folder = os.path.join(
            self.project_folder, pydaw_folder_samplegraph)
        self.timestretch_folder = os.path.join(
            self.project_folder, pydaw_folder_timestretch)
        self.glued_folder = os.path.join(
            self.project_folder, pydaw_folder_glued)
        self.user_folder = os.path.join(
            self.project_folder, pydaw_folder_user)
        self.backups_folder = os.path.join(
            self.project_folder, pydaw_folder_backups)
        self.samples_folder = os.path.join(
            self.project_folder, pydaw_folder_samples)
        self.backups_file = os.path.join(
            self.project_folder, pydaw_file_backups)
        self.plugin_pool_folder = os.path.join(
            self.project_folder, pydaw_folder_plugins)
        self.projects_folder = os.path.join(
            self.project_folder, pydaw_folder_projects)
        self.plugin_uid_file = os.path.join(
            self.project_folder, pydaw_file_plugin_uid)
        self.pywavs_file = os.path.join(
            self.project_folder, pydaw_file_pywavs)
        self.pystretch_file = os.path.join(
            self.project_folder, pydaw_file_pystretch)
        self.pystretch_map_file = os.path.join(
            self.project_folder, pydaw_file_pystretch_map)

        self.project_folders = [
            self.audio_folder, self.audio_tmp_folder, self.samples_folder,
            self.samplegraph_folder, self.timestretch_folder,
            self.glued_folder, self.user_folder, self.projects_folder,
            self.backups_folder, self.plugin_pool_folder,
            self.audio_rec_folder]

        pydaw_clear_sample_graph_cache()

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)
        else:
            self.open_stretch_dicts()

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            print(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

        f_version = pydaw_read_file_text(os.path.join(
            INSTALL_PREFIX, "lib", global_pydaw_version_string,
            "minor-version.txt"))
        self.create_file(
            "", "version.txt",
            "Created with {}-{}".format(
                global_pydaw_version_string, f_version))
        self.create_file(
            "", os.path.basename(a_project_file),
            "This file is not supposed to contain any data, it is "
            "only a placeholder for saving and opening the project")
        self.create_file("", pydaw_file_pywavs, pydaw_terminating_char)
        self.create_file("", pydaw_file_pystretch_map, pydaw_terminating_char)
        self.create_file("", pydaw_file_pystretch, pydaw_terminating_char)

        self.open_stretch_dicts()
        #self.commit("Created project")

    def save_project_as(self, a_file_name):
        f_file_name = str(a_file_name)
        print("Saving project as {} ...".format(f_file_name))
        f_new_project_folder = os.path.dirname(f_file_name)
        #The below is safe because we already checked that the folder
        #should be empty before calling this
        shutil.rmtree(f_new_project_folder)
        shutil.copytree(self.project_folder, f_new_project_folder)
#        self.set_project_folders(f_file_name)
#        self.this_pydaw_osc.pydaw_open_song(self.project_folder)

    def get_next_plugin_uid(self):
        if os.path.isfile(self.plugin_uid_file):
            with open(self.plugin_uid_file) as f_handle:
                f_result = int(f_handle.read())
            f_result += 1
            with open(self.plugin_uid_file, "w", newline="\n") as f_handle:
                f_handle.write(str(f_result))
            assert(f_result < 100000)
            return f_result
        else:
            with open(self.plugin_uid_file, "w", newline="\n") as f_handle:
                f_handle.write(str(0))
            return 0

    def fix_backup_names(self):
        """ Hack to fix invalid ':' chars in Windows file names,
            can be removed at MusiKernel_v2
        """
        f_found = False
        for f_name in (x for x in os.listdir(self.backups_folder)
        if  ":" in x and x.endswith(".tar.bz2")):
            f_old = os.path.join(self.backups_folder, f_name)
            f_new = os.path.join(self.backups_folder, f_name.replace(":", "-"))
            print("Renaming {} -- to -- {}".format(f_old, f_new))
            shutil.move(f_old, f_new)
            f_found = True
        if not f_found:
            print("History was clean, not modifying anything")
            return
        # Also clean up the history tree
        f_history = self.get_backups_history()
        if not f_history:
            return
        print('Old f_history["CURRENT"] = {}'.format(f_history["CURRENT"]))
        f_history["CURRENT"] = f_history["CURRENT"].replace(":", "-")
        print('New f_history["CURRENT"] = {}'.format(f_history["CURRENT"]))
        # breadth-first search to fix the file names
        fifo = collections.deque([f_history["NODES"]])
        while fifo:
            f_node = fifo.popleft()
            for k, v in list(f_node.items()):
                assert isinstance(k, str), str(f_history)
                assert isinstance(v, dict), str(f_history)
                if ":" in k:
                    f_node[k.replace(":", "-")] = v
                    f_node.pop(k)
                if v:
                    fifo.append(v)
        print("New f_history:  {}".format(f_history))
        self.save_backups_history(f_history)

    def create_backup(self, a_name=None):
        self.fix_backup_names()
        f_backup_name = a_name if a_name else \
            datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.tar.bz2")
        f_file_path = os.path.join(self.backups_folder, f_backup_name)
        if os.path.exists(f_file_path):
            print("create_backup:  '{}' exists".format(f_file_path))
            return False
        with tarfile.open(f_file_path, "w:bz2") as f_tar:
            f_tar.add(
                self.projects_folder,
                arcname=os.path.basename(self.projects_folder))
        f_history = self.get_backups_history()
        if f_history:
            try:
                f_node = f_history["NODES"]
                for f_name in (
                x for x in f_history["CURRENT"].split("/") if x):
                    f_node = f_node[f_name]
                f_node[f_backup_name] = {}
                f_history["CURRENT"] = "/".join(
                    [f_history["CURRENT"], f_backup_name])
                self.save_backups_history(f_history)
            except Exception as ex:
                print("ERROR:  create_backup() failed {}".format(ex))
                print("Resetting project history")
                self.save_backups_history(
                    {"NODES":{f_backup_name:{}}, "CURRENT":f_backup_name})
        else:
            self.save_backups_history(
                {"NODES":{f_backup_name:{}}, "CURRENT":f_backup_name})
        return True

    def get_backups_history(self):
        if os.path.exists(self.backups_file):
            with open(self.backups_file) as f_handle:
                return json.load(f_handle)
        else:
            return None

    def save_backups_history(self, a_struct):
        with open(self.backups_file, "w", newline="\n") as f_handle:
            json.dump(
                a_struct, f_handle, sort_keys=True, indent=4,
                separators=(',', ': '))

    def show_project_history(self):
        self.create_backup()
        f_file = os.path.join(self.project_folder, "default.musikernel")
        subprocess.Popen([PYTHON3, PROJECT_HISTORY_SCRIPT, f_file])

    def get_next_glued_file_name(self):
        while True:
            self.glued_name_index += 1
            f_path = os.path.join(
                self.glued_folder,
                "glued-{}.wav".format(self.glued_name_index))
            if not os.path.isfile(f_path):
                break
        return f_path

    def open_stretch_dicts(self):
        self.timestretch_cache = {}
        self.timestretch_reverse_lookup = {}

        f_cache_text = pydaw_read_file_text(self.pystretch_file)
        for f_line in f_cache_text.split("\n"):
            if f_line == pydaw_terminating_char:
                break
            f_line_arr = f_line.split("|", 5)
            f_file_path_and_uid = f_line_arr[5].split("|||")
            self.timestretch_cache[
                (int(f_line_arr[0]), float(f_line_arr[1]),
                float(f_line_arr[2]), float(f_line_arr[3]),
                float(f_line_arr[4]),
                f_file_path_and_uid[0])] = int(f_file_path_and_uid[1])

        f_map_text = pydaw_read_file_text(self.pystretch_map_file)
        for f_line in f_map_text.split("\n"):
            if f_line == pydaw_terminating_char:
                break
            f_line_arr = f_line.split("|||")
            self.timestretch_reverse_lookup[f_line_arr[0]] = f_line_arr[1]

    def save_stretch_dicts(self):
        f_stretch_text = ""
        for k, v in list(self.timestretch_cache.items()):
            for f_tuple_val in k:
                f_stretch_text += "{}|".format(f_tuple_val)
            f_stretch_text += "||{}\n".format(v)
        f_stretch_text += pydaw_terminating_char
        self.save_file("", pydaw_file_pystretch, f_stretch_text)

        f_map_text = ""
        for k, v in list(self.timestretch_reverse_lookup.items()):
            f_map_text += "{}|||{}\n".format(k, v)
        f_map_text += pydaw_terminating_char
        self.save_file("", pydaw_file_pystretch_map, f_map_text)

    def get_wavs_dict(self):
        try:
            f_file = open(self.pywavs_file, "r")
        except:
            return pydaw_name_uid_dict()
        f_str = f_file.read()
        f_file.close()
        return pydaw_name_uid_dict.from_str(f_str)

    def save_wavs_dict(self, a_uid_dict):
        pydaw_write_file_text(self.pywavs_file, str(a_uid_dict))
        #self.save_file("", pydaw_file_pywavs, str(a_uid_dict))


    def timestretch_lookup_orig_path(self, a_path):
        if a_path in self.timestretch_reverse_lookup:
            return self.timestretch_reverse_lookup[a_path]
        else:
            return a_path

    def timestretch_audio_item(self, a_audio_item):
        """ Return path, uid for a time-stretched
            audio item and update all project files,
            or None if the UID already exists in the cache
        """
        a_audio_item.timestretch_amt = round(
            a_audio_item.timestretch_amt, 6)
        a_audio_item.pitch_shift = round(a_audio_item.pitch_shift, 6)
        a_audio_item.timestretch_amt_end = round(
            a_audio_item.timestretch_amt_end, 6)
        a_audio_item.pitch_shift_end = round(a_audio_item.pitch_shift_end, 6)

        f_src_path = self.get_wav_name_by_uid(a_audio_item.uid)
        if f_src_path in self.timestretch_reverse_lookup:
            f_src_path = self.timestretch_reverse_lookup[f_src_path]
        else:
            if (a_audio_item.timestretch_amt == 1.0 and \
            a_audio_item.pitch_shift == 0.0 and \
            a_audio_item.timestretch_amt_end == 1.0 and \
            a_audio_item.pitch_shift_end == 0.0) or \
            (a_audio_item.time_stretch_mode == 1 and \
            a_audio_item.pitch_shift == a_audio_item.pitch_shift_end) or \
            (a_audio_item.time_stretch_mode == 2 and \
            a_audio_item.timestretch_amt == a_audio_item.timestretch_amt_end):
                #Don't process if the file is not being stretched/shifted yet
                return None
        f_key = (a_audio_item.time_stretch_mode, a_audio_item.timestretch_amt,
                 a_audio_item.pitch_shift, a_audio_item.timestretch_amt_end,
                 a_audio_item.pitch_shift_end, a_audio_item.crispness,
                 f_src_path)
        if f_key in self.timestretch_cache:
            a_audio_item.uid = self.timestretch_cache[f_key]
            return None
        else:
            f_wavs_dict = self.get_wavs_dict()
            f_uid = f_wavs_dict.gen_file_name_uid()
            f_dest_path = os.path.join(
                self.timestretch_folder, "{}.wav".format(f_uid))

            f_cmd = None
            if a_audio_item.time_stretch_mode == 1:
                libmk.IPC.pydaw_pitch_env(
                    f_src_path, f_dest_path, a_audio_item.pitch_shift,
                    a_audio_item.pitch_shift_end)
                #add it to the pool
                self.get_wav_uid_by_name(f_dest_path, a_uid=f_uid)
            elif a_audio_item.time_stretch_mode == 2:
                libmk.IPC.pydaw_rate_env(
                    f_src_path, f_dest_path, a_audio_item.timestretch_amt,
                    a_audio_item.timestretch_amt_end)
                #add it to the pool
                self.get_wav_uid_by_name(f_dest_path, a_uid=f_uid)
            elif a_audio_item.time_stretch_mode == 3:
                f_cmd = [
                    pydaw_rubberband_util, "-c", str(a_audio_item.crispness),
                    "-t", str(a_audio_item.timestretch_amt), "-p",
                    str(a_audio_item.pitch_shift), "-R", "--pitch-hq",
                    f_src_path, f_dest_path]
            elif a_audio_item.time_stretch_mode == 4:
                f_cmd = [
                    pydaw_rubberband_util, "-F", "-c",
                    str(a_audio_item.crispness), "-t",
                    str(a_audio_item.timestretch_amt), "-p",
                    str(a_audio_item.pitch_shift), "-R", "--pitch-hq",
                    f_src_path, f_dest_path]
            elif a_audio_item.time_stretch_mode == 5:
                f_cmd = [
                    pydaw_sbsms_util, f_src_path, f_dest_path,
                    str(1.0 / a_audio_item.timestretch_amt),
                    str(1.0 / a_audio_item.timestretch_amt_end),
                    str(a_audio_item.pitch_shift),
                    str(a_audio_item.pitch_shift_end) ]
            elif a_audio_item.time_stretch_mode == 6:
                if a_audio_item.pitch_shift != 0.0:
                    f_cmd = [
                        pydaw_paulstretch_util, "-s",
                        str(a_audio_item.timestretch_amt), "-p",
                        str(a_audio_item.pitch_shift), f_src_path, f_dest_path
                        ]
                else:
                    f_cmd = [
                        pydaw_paulstretch_util, "-s",
                        str(a_audio_item.timestretch_amt), f_src_path,
                        f_dest_path
                        ]
                if pydaw_util.IS_WINDOWS:
                    f_cmd.insert(0, pydaw_util.PYTHON3)

            self.timestretch_cache[f_key] = f_uid
            self.timestretch_reverse_lookup[f_dest_path] = f_src_path
            a_audio_item.uid = self.timestretch_cache[f_key]

            if f_cmd is not None:
                print("Running {}".format(" ".join(f_cmd)))
                f_proc = subprocess.Popen(f_cmd)
                return f_dest_path, f_uid, f_proc
            else:
                return None

    def timestretch_get_orig_file_uid(self, a_uid):
        """ Return the UID of the original file """
        f_new_path = self.get_wav_path_by_uid(a_uid)
        if f_new_path in self.timestretch_reverse_lookup:
            f_old_path = self.timestretch_reverse_lookup[f_new_path]
            return self.get_wav_uid_by_name(f_old_path)
        else:
            print("\n####\n####\nWARNING:  "
                "timestretch_get_orig_file_uid could not find uid {}"
                "\n####\n####\n".format(a_uid))
            return a_uid


    def get_sample_graph_by_name(self, a_path, a_uid_dict=None, a_cp=True):
        f_uid = self.get_wav_uid_by_name(a_path, a_cp=a_cp)
        return self.get_sample_graph_by_uid(f_uid)

    def get_sample_graph_by_uid(self, a_uid):
        f_pygraph_file = os.path.join(
            *(str(x) for x in (self.samplegraph_folder, a_uid)))
        f_result = pydaw_sample_graph.create(
            f_pygraph_file, self.samples_folder)
        if not f_result.is_valid(): # or not f_result.check_mtime():
            print("\n\nNot valid, or else mtime is newer than graph time, "
                  "deleting sample graph...\n")
            pydaw_remove_item_from_sg_cache(f_pygraph_file)
            self.create_sample_graph(self.get_wav_path_by_uid(a_uid), a_uid)
            return pydaw_sample_graph.create(
                f_pygraph_file, self.samples_folder)
        else:
            return f_result

    def delete_sample_graph_by_name(self, a_path):
        f_uid = self.get_wav_uid_by_name(a_path, a_cp=False)
        self.delete_sample_graph_by_uid(f_uid)

    def delete_sample_graph_by_uid(self, a_uid):
        f_pygraph_file = os.path.join(
            *(str(x) for x in (self.samplegraph_folder, a_uid)))
        pydaw_remove_item_from_sg_cache(f_pygraph_file)

    def get_wav_uid_by_name(self, a_path, a_uid_dict=None,
                            a_uid=None, a_cp=True):
        """ Return the UID from the wav pool, or add to the
            pool if it does not exist
        """
        if a_uid_dict is None:
            f_uid_dict = self.get_wavs_dict()
        else:
            f_uid_dict = a_uid_dict
        if pydaw_util.IS_WINDOWS:
            f_path = str(a_path)
        else:
            f_path = str(a_path).replace("//", "/")
        if a_cp:
            self.cp_audio_file_to_cache(f_path)
        if f_uid_dict.name_exists(f_path):
            return f_uid_dict.get_uid_by_name(f_path)
        else:
            f_uid = f_uid_dict.add_new_item(f_path, a_uid)
            self.create_sample_graph(f_path, f_uid)
            self.save_wavs_dict(f_uid_dict)
            return f_uid

    def cp_audio_file_to_cache(self, a_file):
        if a_file in self.cached_audio_files:
            return
        if a_file[0] != "/" and a_file[1] == ":":
            f_file = a_file.replace(":", "", 1)
            f_cp_path = os.path.join(self.samples_folder, f_file)
        else:
            # Work around some baffling Python behaviour where
            # os.path.join('/lala/la', '/ha/haha') returns '/ha/haha'
            if a_file[0] == '/':
                f_cp_path = "".join([self.samples_folder, a_file])
            else:
                f_cp_path = os.path.join(self.samples_folder, a_file)
        f_cp_path = os.path.normpath(f_cp_path)
        f_cp_dir = os.path.dirname(f_cp_path)
        if not os.path.isdir(f_cp_dir):
            os.makedirs(f_cp_dir)
        if not os.path.isfile(f_cp_path):
            shutil.copy(a_file, f_cp_path)
        self.cached_audio_files.append(a_file)

    def get_wav_name_by_uid(self, a_uid, a_uid_dict=None):
        """ Return the UID from the wav pool, or add to the
            pool if it does not exist
        """
        if a_uid_dict is None:
            f_uid_dict = self.get_wavs_dict()
        else:
            f_uid_dict = a_uid_dict
        if f_uid_dict.uid_exists(a_uid):
            return f_uid_dict.get_name_by_uid(a_uid)
        else:
            raise Exception

    def get_wav_path_by_uid(self, a_uid):
        f_uid_dict = self.get_wavs_dict()
        return f_uid_dict.get_name_by_uid(a_uid)

    def create_sample_graph(self, a_path, a_uid):
        f_uid = int(a_uid)
        a_path = pydaw_util.pi_path(a_path)
        f_sample_dir_path = "{}{}".format(self.samples_folder, a_path)
        if os.path.isfile(a_path):
            f_path = a_path
        elif os.path.isfile(f_sample_dir_path):
            f_path = f_sample_dir_path
        else:
            raise Exception("Cannot create sample graph, the "
                "following do not exist:\n{}\n{}\n".format(
                a_path, f_sample_dir_path))
        libmk.IPC.pydaw_add_to_wav_pool(f_path, f_uid)


    def copy_plugin(self, a_old, a_new):
        f_old_path = os.path.join(
            *(str(x) for x in (self.plugin_pool_folder, a_old)))
        if os.path.exists(f_old_path):
            with open(f_old_path) as file_handle:
                self.save_file(
                    pydaw_folder_plugins, a_new, file_handle.read())
                #self.commit("Copy plugin UID {} to {}".format(a_old, a_new))
        else:
            print("{} does not exist, not copying".format(f_old_path))


class pydaw_abstract_midi_event:
    """ Allows inheriting classes to be sorted by .start variable
    , which is left to the iheriter's to implement"""
    def __lt__(self, other):
        return self.start < other.start

class pydaw_note(pydaw_abstract_midi_event):
    def __init__(self, a_start, a_length, a_note_number, a_velocity):
        self.start = round(float(a_start), 6)
        self.length = round(float(a_length), 6)
        self.velocity = int(a_velocity)
        self.note_num = int(a_note_number)
        self.is_selected = False
        self.set_end()

    def __eq__(self, other):
        return(
            (self.start == other.start) and \
            (self.note_num == other.note_num) and \
            (self.length == other.length) and \
            (self.velocity == other.velocity))

    def set_start(self, a_start):
        self.start = round(float(a_start), 6)
        self.set_end()

    def set_length(self, a_length):
        self.length = round(float(a_length), 6)
        self.set_end()

    def set_end(self):
        self.end = round(self.length + self.start, 6)

    def overlaps(self, other):
        if self.note_num == other.note_num:
            if other.start >= self.start and other.start < self.end:
                return True
            elif other.start < self.start and other.end > self.start:
                return True
        return False

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_note(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_note.from_arr(f_arr[1:])

    def __str__(self):
        return "|".join(str(x) for x in
            ("n", round(self.start, 6), round(self.length, 6),
             self.note_num, self.velocity))

    def clone(self):
        return pydaw_note.from_str(str(self))


class pydaw_cc(pydaw_abstract_midi_event):
    def __init__(self, a_start, a_cc_num, a_cc_val):
        self.start = round(float(a_start), 6)
        self.cc_num = int(a_cc_num)
        self.cc_val = round(float(a_cc_val), 6)

    def __eq__(self, other):
        return ((self.start == other.start) and
        (self.cc_num == other.cc_num) and (self.cc_val == other.cc_val))

    def set_val(self, a_val):
        self.cc_val = pydaw_clip_value(float(a_val), 0.0, 127.0, True)

    def __str__(self):
        return "|".join(str(x) for x in
            ("c", round(self.start, 6), self.cc_num, round(self.cc_val, 6)))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_cc(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_cc.from_arr(f_arr[1:])

    def clone(self):
        return pydaw_cc.from_str(str(self))


class pydaw_pitchbend(pydaw_abstract_midi_event):
    def __init__(self, a_start, a_pb_val):
        self.start = round(float(a_start), 6)
        self.pb_val = round(float(a_pb_val), 6)

    def __eq__(self, other):
        #TODO:  get rid of the pb_val comparison?
        return ((self.start == other.start) and (self.pb_val == other.pb_val))

    def set_val(self, a_val):
        self.pb_val = pydaw_clip_value(float(a_val), -1.0, 1.0, True)

    def __str__(self):
        return "|".join(str(x) for x in
            ("p", self.start, round(self.pb_val, 6)))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_pitchbend(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_pitchbend.from_arr(f_arr[1:])

    def clone(self):
        return pydaw_pitchbend.from_str(str(self))

class pydaw_tracks:
    def __init__(self):
        self.tracks = {}

    def reorder(self, a_dict):
        self.tracks = {a_dict[k]:self.tracks[k] for k in sorted(self.tracks)}
        for k, v in self.tracks.items():
            v.track_uid = v.track_pos = k

    def add_track(self, a_index, a_track):
        self.tracks[int(a_index)] = a_track

    def get_names(self):
        return [self.tracks[k].name for k in sorted(self.tracks)]

    def __str__(self):
        f_result = "".join(str(self.tracks[k]) for k in sorted(self.tracks))
        f_result += pydaw_terminating_char
        return f_result

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_tracks()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if not f_line == pydaw_terminating_char:
                f_line_arr = f_line.split("|")
                f_result.add_track(f_line_arr[0], pydaw_track(*f_line_arr))
        return f_result

class pydaw_track:
    def __init__(self, a_track_uid=-1, a_solo=False, a_mute=False,
                 a_track_pos=-1, a_name="track"):
        self.track_uid = int(a_track_uid)
        self.name = str(a_name)
        self.solo = int_to_bool(a_solo)
        self.mute = int_to_bool(a_mute)
        self.set_track_pos(a_track_pos)

    # TODO:  WTH does this do???  Was this supposed to be "show at pos?"
    def set_track_pos(self, a_track_pos):
        self.track_pos = int(a_track_pos)
        assert(self.track_pos >= 0)

    def __str__(self):
        return "{}\n".format("|".join(map(proj_file_str,
            (self.track_uid, bool_to_int(self.solo), bool_to_int(self.mute),
            self.track_pos, self.name))))


class RoutingGraph:
    def __init__(self):
        self.graph = {}

    def reorder(self, a_dict):
        self.graph = {a_dict[k]:v for k, v in self.graph.items()}
        for k, f_dict in self.graph.items():
            for v in f_dict.values():
                v.track_num = k
                v.output = a_dict[v.output]

    def set_node(self, a_index, a_dict):
        self.graph[int(a_index)] = a_dict

    def find_all_paths(self, start, end=0, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if not start in self.graph:
            return []
        paths = []
        for node in (x.output for x in sorted(self.graph[start].values())):
            if node not in path:
                newpaths = self.find_all_paths(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def check_for_feedback(self, a_new, a_old, a_index=None):
        if a_index is not None:
            a_index = int(a_index)
            if a_old in self.graph and a_index in self.graph[a_old]:
                self.graph[a_old].pop(a_index)
        return self.find_all_paths(a_old, a_new)

    def toggle(self, a_src, a_dest, a_sidechain=0):
        f_connected = a_src in self.graph and a_dest in [
            x.output for x in self.graph[a_src].values()
            if x.sidechain == a_sidechain]
        if f_connected:
            for k, v in self.graph[a_src].copy().items():
                if v.output == a_dest and v.sidechain == a_sidechain:
                    self.graph[a_src].pop(k)
        else:
            if self.check_for_feedback(a_src, a_dest):
                return "Can't make connection, it would create a feedback loop"
            if a_src in self.graph and len(self.graph[a_src]) >= 4:
                return ("All available sends already in use for "
                    "track {}".format(a_src))
            if not a_src in self.graph:
                f_i = 0
                self.graph[a_src] = {}
            else:
                for f_i in range(4):
                    if f_i not in self.graph[a_src]:
                        break
            f_result = TrackSend(a_src, f_i, a_dest, a_sidechain)
            self.graph[a_src][f_i] = f_result
            self.set_node(a_src, self.graph[a_src])
        return None

    def set_default_output(self, a_track_num, a_output=0):
        assert(a_track_num != a_output)
        assert(a_track_num != 0)
        if not a_track_num in self.graph or \
        not self.graph[a_track_num]:
            f_send = TrackSend(a_track_num, 0, a_output, 0)
            self.set_node(a_track_num, {0:f_send})
            return True
        else:
            return False

    def sort_all_paths(self):
        f_result = {}
        for f_path in self.graph:
            f_paths = self.find_all_paths(f_path, 0)
            if f_paths:
                f_result[f_path] = max(len(x) for x in f_paths)
            else:
                f_result[f_path] = 0
        return sorted(f_result, key=lambda x: f_result[x], reverse=True)

    def __str__(self):
        f_result = []
        f_sorted = self.sort_all_paths()
        f_result.append("|".join(str(x) for x in ("c", len(f_sorted))))
        for f_index, f_i in zip(f_sorted, range(len(f_sorted))):
            f_result.append("|".join(str(x) for x in ("t", f_index, f_i)))
        for k in sorted(self.graph):
            for v in sorted(self.graph[k].values()):
                f_result.append(str(v))
        f_result.append("\\")
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_str = str(a_str)
        f_result = RoutingGraph()
        f_tracks = {}
        for f_line in f_str.split("\n"):
            if f_line == "\\":
                break
            f_line_arr = f_line.split("|")
            f_uid = int(f_line_arr[1])
            if f_line_arr[0] == "t":
                assert(f_uid not in f_tracks)
                f_tracks[f_uid] = {}
            elif f_line_arr[0] == "s":
                f_send = TrackSend(*f_line_arr[1:])
                f_tracks[f_uid][f_send.index] = f_send
            elif f_line_arr[0] == "c":
                pass
            else:
                assert(False)
        for k, v in f_tracks.items():
            f_result.set_node(k, v)
        return f_result


class TrackSend:
    def __init__(self, a_track_num, a_index, a_output, a_sidechain):
        self.track_num = int(a_track_num)
        self.index = int(a_index)
        self.output = int(a_output)
        # This is actually route type now (->type in the C struct)
        # 0 == normal audio, 1 == sidechain audio, 2 == MIDI
        # TODO:  Rename
        self.sidechain = int(a_sidechain)

    def __str__(self):
        return "|".join(str(x) for x in
            ("s", self.track_num, self.index, self.output, self.sidechain))

    def __lt__(self, other):
        return self.index < other.index


class pydaw_midi_route:
    def __init__(self, a_on, a_track_num, a_device_name):
        self.on = int(a_on)
        self.track_num = int(a_track_num)
        self.device_name = str(a_device_name)

    def __str__(self):
        return "|".join(
            str(x) for x in (self.on, self.track_num, self.device_name))


class pydaw_midi_routings:
    def __init__(self, a_routings=None):
        self.routings = a_routings if a_routings is not None else []

    def __str__(self):
        return "\n".join(str(x) for x in self.routings + ["\\"])

    def reorder(self, a_dict):
        for f_route in self.routings:
            if f_route.track_num in a_dict:
                f_route.track_num = a_dict[f_route.track_num]

    @staticmethod
    def from_str(a_str):
        f_routings = []
        for f_line in a_str.split("\n"):
            if f_line == "\\":
                break
            f_routings.append(pydaw_midi_route(*f_line.split("|", 2)))
        return pydaw_midi_routings(f_routings)


#From old sample_graph..py
AUDIO_ITEM_SCENE_HEIGHT = 900.0
AUDIO_ITEM_SCENE_WIDTH = 3600.0
pydaw_audio_item_scene_rect = QtCore.QRectF(
    0.0, 0.0, AUDIO_ITEM_SCENE_WIDTH, AUDIO_ITEM_SCENE_HEIGHT)

pydaw_audio_item_scene_gradient = QLinearGradient(
    0, 0, 0, AUDIO_ITEM_SCENE_HEIGHT)
pydaw_audio_item_scene_gradient.setColorAt(
    0.0, QColor.fromRgb(60, 60, 60, 120))
pydaw_audio_item_scene_gradient.setColorAt(
    1.0, QColor.fromRgb(30, 30, 30, 120))

pydaw_audio_item_editor_gradient = QLinearGradient(
    0, 0, 0, AUDIO_ITEM_SCENE_HEIGHT)
pydaw_audio_item_editor_gradient.setColorAt(
    0.0, QColor.fromRgb(190, 192, 123, 120))
pydaw_audio_item_editor_gradient.setColorAt(
    1.0, QColor.fromRgb(130, 130, 100, 120))
#end from sample_graph.py

def pydaw_clear_sample_graph_cache():
    global global_sample_graph_cache
    global_sample_graph_cache = {}

def pydaw_remove_item_from_sg_cache(a_path):
    global global_sample_graph_cache
    if os.path.exists(a_path):
        os.remove(a_path)
    if a_path in global_sample_graph_cache:
        global_sample_graph_cache.pop(a_path)
    else:
        print("\n\npydaw_remove_item_from_sg_cache: {} "
            "not found.\n\n".format(a_path))

global_sample_graph_cache = {}

class pydaw_sample_graph:
    @staticmethod
    def create(a_file_name, a_sample_dir):
        """ Used to instantiate a pydaw_sample_graph, but
            grabs from the cache if it already exists...
            Prefer this over directly instantiating.
        """
        f_file_name = str(a_file_name)
        global global_sample_graph_cache
        if f_file_name in global_sample_graph_cache:
            return global_sample_graph_cache[f_file_name]
        else:
            f_result = pydaw_sample_graph(f_file_name, a_sample_dir)
            global_sample_graph_cache[f_file_name] = f_result
            return f_result

    def __init__(self, a_file_name, a_sample_dir):
        """
        a_file_name:  The full path to /.../sample_graphs/uid
        a_sample_dir:  The project's sample dir
        """
        self.sample_graph_cache = None
        f_file_name = str(a_file_name)
        self._file = None
        self.sample_dir = str(a_sample_dir)
        self.sample_dir_file = None
        self.timestamp = None
        self.channels = None
        self.high_peaks = ([],[])
        self.low_peaks = ([],[])
        self.count = None
        self.length_in_seconds = None
        self.sample_rate = None
        self.frame_count = None
        self.peak = 0.0

        if not os.path.isfile(f_file_name):
            return

        try:
            f_file = open(f_file_name, "r")
        except:
            return

        f_line_arr = f_file.readlines()
        f_file.close()
        for f_line in f_line_arr:
            f_line_arr = f_line.split("|")
            if f_line_arr[0] == "\\":
                break
            elif f_line_arr[0] == "meta":
                if f_line_arr[1] == "filename":
                    #Why does this have a newline on the end???
                    self._file = str(f_line_arr[2]).strip("\n")
                    self.sample_dir_file = "{}{}".format(
                        self.sample_dir, self._file)
                elif f_line_arr[1] == "timestamp":
                    self.timestamp = int(f_line_arr[2])
                elif f_line_arr[1] == "channels":
                    self.channels = int(f_line_arr[2])
                elif f_line_arr[1] == "count":
                    self.count = int(f_line_arr[2])
                elif f_line_arr[1] == "length":
                    self.length_in_seconds = float(f_line_arr[2])
                elif f_line_arr[1] == "frame_count":
                    self.frame_count = int(f_line_arr[2])
                elif f_line_arr[1] == "sample_rate":
                    self.sample_rate = int(f_line_arr[2])
            elif f_line_arr[0] == "p":
                f_p_val = float(f_line_arr[3])
                f_abs_p_val = abs(f_p_val)
                if f_abs_p_val > self.peak:
                    self.peak = f_abs_p_val
                if f_p_val > 1.0:
                    f_p_val = 1.0
                elif f_p_val < -1.0:
                    f_p_val = -1.0
                if f_line_arr[2] == "h":
                    self.high_peaks[int(f_line_arr[1])].append(f_p_val)
                elif f_line_arr[2] == "l":
                    self.low_peaks[int(f_line_arr[1])].append(f_p_val)
                else:
                    print("Invalid sample_graph [2] value " + f_line_arr[2])
        for f_list in self.low_peaks:
            f_list.reverse()

        self.low_peaks = [numpy.array(x) for x in self.low_peaks]
        self.high_peaks = [numpy.array(x) for x in self.high_peaks]

        for f_high_peaks, f_low_peaks in zip(self.high_peaks, self.low_peaks):
            numpy.clip(f_high_peaks, 0.01, 0.99, f_high_peaks)
            numpy.clip(f_low_peaks, -0.99, -0.01, f_low_peaks)

    def is_valid(self):
        if (self._file is None):
            print("\n\npydaw_sample_graph.is_valid() "
                "self._file is None {}\n".format(self._file))
            return False
        if self.timestamp is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.timestamp is None {}\n".format(self._file))
            return False
        if self.channels is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.channels is None {}\n".format(self._file))
            return False
        if self.frame_count is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.frame_count is None {}\n".format(self._file))
            return False
        if self.sample_rate is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.sample_rate is None {}\n".format(self._file))
            return False
        return True

    def normalize(self, a_db=0.0):
        if self.peak == 0.0:
            return 0.0
        f_norm_lin = pydaw_db_to_lin(a_db)
        f_diff = f_norm_lin / self.peak
        f_result = round(pydaw_lin_to_db(f_diff), 1)
        f_result = pydaw_clip_value(f_result, -24, 24)
        return f_result

    def create_sample_graph(
            self, a_for_scene=False, a_width=None, a_height=None,
            a_audio_item=None):
        if a_audio_item:
            f_ss = a_audio_item.sample_start * 0.001
            f_se = a_audio_item.sample_end * 0.001
            #f_width_frac = f_se - f_ss
            f_vol = pydaw_util.pydaw_db_to_lin(a_audio_item.vol)
            f_len = len(self.high_peaks[0])
            f_slice_low = int(f_ss * f_len)
            f_slice_high = int(f_se * f_len)
            #a_width *= f_width_frac
        else:
            f_slice_low = None
            f_slice_high = None
        if a_width or a_height or self.sample_graph_cache is None:
            if not a_width:
                a_width = AUDIO_ITEM_SCENE_WIDTH
            if not a_height:
                a_height = AUDIO_ITEM_SCENE_HEIGHT

            if a_for_scene:
                f_width_inc = a_width / self.count
                f_section = a_height / float(self.channels)
            else:
                f_width_inc = 98.0 / self.count
                f_section = 100.0 / float(self.channels)
            f_section_div2 = f_section * 0.5

            f_paths = []

            for f_i in range(self.channels):
                f_result = QPainterPath()
                f_width_pos = 1.0
                f_result.moveTo(f_width_pos, f_section_div2)
                if a_audio_item and a_audio_item.reversed:
                    f_high_peaks = self.high_peaks[f_i][
                            f_slice_high:f_slice_low:-1]
                    f_low_peaks = self.low_peaks[f_i][::-1]
                    f_low_peaks = f_low_peaks[f_slice_low:f_slice_high]
                else:
                    f_high_peaks = self.high_peaks[f_i][
                        f_slice_low:f_slice_high]
                    f_low_peaks = self.low_peaks[f_i][::-1]
                    f_low_peaks = f_low_peaks[f_slice_high:f_slice_low:-1]

                if a_audio_item:
                    f_high_peaks = f_high_peaks * f_vol
                    f_low_peaks = f_low_peaks * f_vol

                for f_peak in f_high_peaks:
                    f_result.lineTo(f_width_pos, f_section_div2 -
                        (f_peak * f_section_div2))
                    f_width_pos += f_width_inc
                for f_peak in f_low_peaks:
                    f_result.lineTo(f_width_pos, (f_peak * -1.0 *
                        f_section_div2) + f_section_div2)
                    f_width_pos -= f_width_inc
                f_result.closeSubpath()
                f_paths.append(f_result)
            if a_width or a_height:
                return f_paths
            self.sample_graph_cache = f_paths
        return self.sample_graph_cache

    def check_mtime(self):
        """ Returns False if the sample graph is older than
            the file modified time

            UPDATE:  Now obsolete, will require some fixing if used again...
        """
        try:
            if os.path.isfile(self._file):
                f_timestamp = int(os.path.getmtime(self._file))
            elif os.path.isfile(self.sample_dir_file):
                #f_timestamp = int(os.path.getmtime(self.sample_dir_file))
                return True
            else:
                raise Exception("Neither original nor cached file exists.")
            return self.timestamp > f_timestamp
        except Exception as f_ex:
            print("\n\nError getting mtime: \n{}\n\n".format(f_ex.message))
            return False

class AudioInputTracks:
    def add_track(self, a_index, a_track):
        self.tracks[a_index] = a_track

    def __init__(self):
        self.tracks = {}

    def __str__(self):
        f_result = []
        for k, v in list(self.tracks.items()):
            f_result.append("{}|{}".format(k, v))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    def reorder(self, a_dict):
        for f_track in self.tracks.values():
            if f_track.output in a_dict:
                print("AudioInputTracks.reorder : {} : {}".format(
                    f_track.output, a_dict[f_track.output]))
                f_track.output = a_dict[f_track.output]

    @staticmethod
    def from_str(a_str):
        f_result = AudioInputTracks()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            else:
                f_line_arr = f_line.split("|")
                f_result.add_track(
                    int(f_line_arr[0]), AudioInputTrack(*f_line_arr[1:]))
        return f_result

class AudioInputTrack:
    def __init__(
            self, a_rec=0, a_monitor=0, a_vol=0.0, a_output=0,
            a_stereo=-1, a_sidechain=0, a_name=""):
        self.rec = int(a_rec)
        self.monitor = int(a_monitor)
        self.output = int(a_output)
        self.vol = float(a_vol)
        self.name = str(a_name)
        self.stereo = int(a_stereo)
        self.sidechain = int(a_sidechain)

    def __str__(self):
        return "|".join(
            str(x) for x in
            (self.rec, self.monitor, self.vol, self.output,
             self.stereo, self.sidechain, self.name))


class MkAudioItem:
    def __init__(
        self,
        a_uid,
        a_sample_start=0.0,
        a_sample_end=1000.0,
        a_start_bar=0,
        a_start_beat=0.0,
        a_timestretch_mode=3,
        a_pitch_shift=0.0,
        a_output_track=0,
        a_vol=0.0,
        a_timestretch_amt=1.0,
        a_fade_in=0.0,
        a_fade_out=999.0,
        a_lane_num=0,
        a_pitch_shift_end=0.0,
        a_timestretch_amt_end=1.0,
        a_reversed=False,
        a_crispness=5,
        a_fadein_vol=-18,
        a_fadeout_vol=-18,
        a_paif_automation_uid=0,
        a_send1=-1,
        a_s1_vol=0.0,
        a_send2=-1,
        a_s2_vol=0.0,
        a_s0_sc=False,
        a_s1_sc=False,
        a_s2_sc=False,
    ):
        self.uid = int(a_uid)
        self.sample_start = float(a_sample_start)
        self.sample_end = float(a_sample_end)
        self.start_bar = int(a_start_bar)
        self.start_beat = float(a_start_beat)
        self.time_stretch_mode = int(a_timestretch_mode)
        self.pitch_shift = float(a_pitch_shift)
        self.output_track = int(a_output_track)
        self.vol = round(float(a_vol), 1)
        self.timestretch_amt = float(a_timestretch_amt)
        self.fade_in = float(a_fade_in)
        self.fade_out = float(a_fade_out)
        self.lane_num = int(a_lane_num)
        self.pitch_shift_end = float(a_pitch_shift_end)
        self.timestretch_amt_end = float(a_timestretch_amt_end)
        if isinstance(a_reversed, bool):
            self.reversed = a_reversed
        else:
            self.reversed = int_to_bool(a_reversed)
        self.crispness = int(a_crispness) #This is specific to Rubberband
        self.fadein_vol = int(a_fadein_vol)
        self.fadeout_vol = int(a_fadeout_vol)
        self.paif_automation_uid = int(a_paif_automation_uid)
        self.send1 = int(a_send1)
        self.s1_vol = round(float(a_s1_vol), 1)
        self.send2 = int(a_send2)
        self.s2_vol = round(float(a_s2_vol), 1)
        self.s0_sc = int_to_bool(a_s0_sc)
        self.s1_sc = int_to_bool(a_s1_sc)
        self.s2_sc = int_to_bool(a_s2_sc)

    def set_pos(self, a_bar, a_beat):
        self.start_bar = int(a_bar)
        self.start_beat = float(a_beat)

    def set_fade_in(self, a_value):
        f_value = pydaw_clip_value(a_value, 0.0, self.fade_out - 1.0)
        self.fade_in = f_value

    def set_fade_out(self, a_value):
        f_value = pydaw_clip_value(a_value, self.fade_in + 1.0, 999.0)
        self.fade_out = f_value

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return "|".join(proj_file_str(x) for x in
            (self.uid, self.sample_start, self.sample_end,
            self.start_bar, self.start_beat,
            self.time_stretch_mode, self.pitch_shift, self.output_track,
            self.vol, self.timestretch_amt,
            self.fade_in, self.fade_out, self.lane_num, self.pitch_shift_end,
            self.timestretch_amt_end, bool_to_int(self.reversed),
            int(self.crispness), int(self.fadein_vol), int(self.fadeout_vol),
            int(self.paif_automation_uid),
            self.send1, self.s1_vol, self.send2, self.s2_vol,
            bool_to_int(self.s0_sc), bool_to_int(self.s1_sc),
            bool_to_int(self.s2_sc)))


class MkTakes:
    def __init__(self):
        self._dict = {}   # map take uid to a list of item uids
        self._lookup = {}  # map item uid to take uid

    def get_take_uid(self, a_item_uid):
        a_item_uid = int(a_item_uid)
        if a_item_uid in self._lookup:
            return self._lookup[a_item_uid]
        else:
            return None

    def get_take(self, a_item_uid):
        result = self.get_take_uid(a_item_uid)
        return None if result is None else (result, self._dict[result])

    def set_take(self, a_item_uid_list, a_take_uid=None):
        assert isinstance(a_item_uid_list, list)
        if a_take_uid is None:  #auto-assign a new value
            if self._dict:
                a_take_uid = max(self._dict) + 1
            else:
                a_take_uid = 0
        else:
            a_take_uid = int(a_take_uid)
        self._dict[a_take_uid] = a_item_uid_list
        for f_uid in a_item_uid_list:
            self._lookup[f_uid] = a_take_uid

    def add_item(self, a_orig_uid, a_new_uid):
        a_orig_uid, a_new_uid = (int(x) for x in (a_orig_uid, a_new_uid))
        f_take = self.get_take(a_orig_uid)
        if f_take:
            f_take_uid, f_take = f_take
            if a_new_uid not in f_take:
                f_take.append(a_new_uid)
                self.set_take(f_take, f_take_uid)
        else:
            f_take = [a_orig_uid, a_new_uid]
            self.set_take(f_take)

    def __str__(self):
        result = []
        for k in sorted(self._dict):
            v = self._dict[k]
            result.append("|".join(str(x) for x in [k] + v))
        return "\n".join(result)

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_str(a_str):
        result = MkTakes()
        for row in ([int(y) for y in x.split("|")] for x in a_str.split("\n")):
            key = row[0]
            value = row[1:]
            result._dict[key] = value
            for f_uid in value:
                result._lookup[f_uid] = key
        return result

