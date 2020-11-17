from .sample_graph import (
    pydaw_clear_sample_graph_cache,
    pydaw_remove_item_from_sg_cache,
    pydaw_sample_graph,
)
from mkpy import libmk
from mkpy.libpydaw import *
from mkpy.libpydaw.pydaw_util import *
import collections
import datetime
import json
import os
import shutil
import tarfile


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


