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

import os
import re
import traceback

import numpy

import libmk

from libmk.mk_project import *

from libpydaw.pydaw_util import *
from libpydaw.translate import _
from libpydaw.pydaw_widgets import pydaw_modulex_settings

from libdawnext.osc import DawNextOsc

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

from libpydaw import pydaw_history

import mkplugins

TRACK_COUNT_ALL = 32
MAX_AUDIO_ITEM_COUNT = 256

PIXMAP_TILE_WIDTH = 4000

PIXMAP_BEAT_WIDTH = 48
PIXMAP_TILE_HEIGHT = 32

pydaw_folder_dawnext = os.path.join("projects", "dawnext")
pydaw_folder_items = os.path.join(pydaw_folder_dawnext, "items")
pydaw_folder_tracks = os.path.join(pydaw_folder_dawnext, "tracks")

FILE_SEQUENCER = os.path.join(pydaw_folder_dawnext, "sequencer.txt")
pydaw_file_regions_atm = os.path.join(pydaw_folder_dawnext, "automation.txt")
pydaw_file_routing_graph = os.path.join(pydaw_folder_dawnext, "routing.txt")
pydaw_file_midi_routing = os.path.join(
    pydaw_folder_dawnext, "midi_routing.txt")
pydaw_file_pyitems = os.path.join(pydaw_folder_dawnext, "items.txt")
pydaw_file_takes = os.path.join(pydaw_folder_dawnext, "takes.txt")
pydaw_file_pytracks = os.path.join(pydaw_folder_dawnext, "tracks.txt")
pydaw_file_pyinput = os.path.join(pydaw_folder_dawnext, "input.txt")
pydaw_file_notes = os.path.join(pydaw_folder_dawnext, "notes.txt")

#Anything smaller gets deleted when doing a transform
pydaw_min_note_length = 4.0 / 129.0


class DawNextProject(libmk.AbstractProject):
    def __init__(self, a_with_audio):
        self.undo_context = 0
        self.TRACK_COUNT = TRACK_COUNT_ALL
        self.last_item_number = 1
        self.last_region_number = 1
        self.clear_history()
        self.painter_path_cache = {}
        self.pixmap_cache_unscaled = {}
        self.IPC = DawNextOsc(a_with_audio)
        self.suppress_updates = False

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        f_result = libmk.AbstractProject.save_file(
            self, a_folder, a_file, a_text, a_force_new)
        if f_result:
            f_existed, f_old = f_result
            f_history_file = pydaw_history.pydaw_history_file(
                a_folder, a_file, a_text, f_old, f_existed)
            self.history_files.append(f_history_file)
            if not pydaw_util.IS_A_TTY:
                print(str(f_history_file))

    def set_undo_context(self, a_context):
        self.undo_context = a_context

    def clear_undo_context(self, a_context):
        self.history_commits[a_context] = []

    def commit(self, a_message, a_discard=False):
        """ Commit the project history """
        if self.undo_context not in self.history_commits:
            self.history_commits[self.undo_context] = []
        if self.history_undo_cursor > 0:
            self.history_commits[self.undo_context] = self.history_commits[
                self.undo_context][:self.history_undo_cursor]
            self.history_undo_cursor = 0
        if self.history_files and not a_discard:
            f_commit = pydaw_history.pydaw_history_commit(
                self.history_files, a_message)
            self.history_commits[self.undo_context].append(f_commit)
        self.history_files = []

    def clear_history(self):
        self.history_undo_cursor = 0
        self.history_files = []
        self.history_commits = {}

    def undo(self):
        if self.undo_context not in self.history_commits or \
        self.history_undo_cursor >= len(
        self.history_commits[self.undo_context]):
            return False
        self.history_undo_cursor += 1
        self.history_commits[self.undo_context][
            -1 * self.history_undo_cursor].undo(self.project_folder)
        self.clear_caches()
        return True

    def redo(self):
        if self.undo_context not in self.history_commits or \
        self.history_undo_cursor == 0:
            return False
        self.history_commits[self.undo_context][
            -1 * self.history_undo_cursor].redo(self.project_folder)
        self.history_undo_cursor -= 1
        self.clear_caches()
        return True

    def get_files_dict(self, a_folder, a_ext=None):
        f_result = {}
        f_files = []
        if a_ext is not None :
            for f_file in os.listdir(a_folder):
                if f_file.endswith(a_ext):
                    f_files.append(f_file)
        else:
            f_files = os.listdir(a_folder)
        for f_file in f_files:
            f_result[f_file] = pydaw_read_file_text(
                os.path.join(a_folder, f_file))
        return f_result

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]
        self.items_folder = os.path.join(
            self.project_folder, pydaw_folder_items)
        self.host_folder = os.path.join(
            self.project_folder, pydaw_folder_dawnext)
        self.track_pool_folder = os.path.join(
            self.project_folder, pydaw_folder_tracks)
        #files
        self.sequencer_file = os.path.join(
            self.project_folder, FILE_SEQUENCER)
        self.pyitems_file = os.path.join(
            self.project_folder, pydaw_file_pyitems)
        self.takes_file = os.path.join(
            self.project_folder, pydaw_file_takes)
        self.pyscale_file = os.path.join(
            self.project_folder, "default.pyscale")
        self.pynotes_file = os.path.join(
            self.project_folder, pydaw_file_notes)
        self.routing_graph_file = os.path.join(
            self.project_folder, pydaw_file_routing_graph)
        self.midi_routing_file = os.path.join(
            self.project_folder, pydaw_file_midi_routing)
        self.automation_file = os.path.join(
            self.project_folder, pydaw_file_regions_atm)
        self.audio_inputs_file = os.path.join(
            self.project_folder, pydaw_file_pyinput)

        self.project_folders = [
            self.project_folder, self.items_folder, self.track_pool_folder,]

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

        if a_notify_osc:
            self.IPC.pydaw_open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            print(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

        self.save_file("", FILE_SEQUENCER, str(pydaw_sequencer()))
        self.create_file("", pydaw_file_pyitems, pydaw_terminating_char)
        f_tracks = pydaw_tracks()
        for i in range(TRACK_COUNT_ALL):
            f_tracks.add_track(i, pydaw_track(
                a_track_uid=i, a_track_pos=i,
                a_name="Master" if i == 0 else "track{}".format(i)))
            plugins = libmk.pydaw_track_plugins()
            for i2 in range(mkplugins.TOTAL_PLUGINS_PER_TRACK):
                plugins.plugins.append(libmk.pydaw_track_plugin(i2, 0, -1))
            self.save_track_plugins(i, plugins)

        self.create_file("", pydaw_file_pytracks, str(f_tracks))

        self.commit("Created project")
        if a_notify_osc:
            self.IPC.pydaw_open_song(self.project_folder)

    def active_wav_pool_uids(self):
        f_region = self.get_region()
        f_item_uids = set(x.item_uid for x in f_region.items)
        f_items = [self.get_item_by_uid(x) for x in f_item_uids]
        result = set(y.uid for x in f_items for y in x.items.values())
        for uid in self.get_plugin_wav_pool_uids():
            result.add(uid)
        return result

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return pydaw_read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        pydaw_write_file_text(self.pynotes_file, a_text)

    def set_midi_scale(self, a_key, a_scale):
        pydaw_write_file_text(
            self.pyscale_file, "{}|{}".format(a_key, a_scale))

    def get_midi_scale(self):
        if os.path.exists(self.pyscale_file):
            f_list = pydaw_read_file_text(self.pyscale_file).split("|")
            return (int(f_list[0]), int(f_list[1]))
        else:
            return None

    def get_routing_graph(self):
        if os.path.isfile(self.routing_graph_file):
            with open(self.routing_graph_file) as f_handle:
                return RoutingGraph.from_str(f_handle.read())
        else:
            return RoutingGraph()

    def save_routing_graph(self, a_graph, a_notify=True):
        self.save_file("", pydaw_file_routing_graph, str(a_graph))
        if a_notify:
            self.IPC.pydaw_update_track_send()

    def check_output(self, a_track=None):
        """ Ensure that any track with items or plugins is routed to master
            if it does not have any routings
        """
        if a_track is not None and a_track <= 0:
            return
        graph = self.get_routing_graph()
        region = self.get_region()
        modified = False
        tracks = set(x.track_num for x in region.items)
        if 0 in tracks:
            tracks.remove(0)
        if a_track is not None:
            tracks.add(a_track)

        for i in tracks:
            if graph.set_default_output(i):
                modified = True

        if modified:
            self.save_routing_graph(graph)
            self.commit("Set default output")

    def get_midi_routing(self):
        if os.path.isfile(self.midi_routing_file):
            with open(self.midi_routing_file) as f_handle:
                return pydaw_midi_routings.from_str(f_handle.read())
        else:
            return pydaw_midi_routings()

    def save_midi_routing(self, a_routing, a_notify=True):
        self.save_file("", pydaw_file_midi_routing, str(a_routing))
        if a_notify:
            self.commit("Update MIDI routing")

    def get_takes(self):
        if os.path.isfile(self.takes_file):
            with open(self.takes_file) as fh:
                return MkTakes.from_str(fh.read())
        else:
            return MkTakes()

    def save_takes(self, a_takes):
        self.save_file("", pydaw_file_takes, str(a_takes))

    def get_items_dict(self):
        try:
            f_file = open(self.pyitems_file, "r")
        except:
            return pydaw_name_uid_dict()
        f_str = f_file.read()
        f_file.close()
        return pydaw_name_uid_dict.from_str(f_str)

    def save_items_dict(self, a_uid_dict):
        self.save_file("", pydaw_file_pyitems, str(a_uid_dict))

    def get_region(self):
        if os.path.isfile(self.sequencer_file):
            with open(self.sequencer_file) as f_file:
                return pydaw_sequencer.from_str(f_file.read())
        else:
            return pydaw_sequencer()

    def import_midi_file(
            self, a_midi_file, a_beat_offset, a_track_offset):
        """ @a_midi_file:  An instance of DawNextMidiFile """
        f_sequencer = self.get_region()
        f_active_tracks = [x + a_track_offset for x in
            a_midi_file.result_dict if x + a_track_offset < TRACK_COUNT_ALL]
        f_end_beat = max(x.get_length() for x in
            a_midi_file.result_dict.values())
        f_sequencer.clear_range(f_active_tracks, a_beat_offset, f_end_beat)
        for k,v in a_midi_file.result_dict.items():
            f_track = a_track_offset + int(k)
            if f_track >= TRACK_COUNT_ALL:
                break
            f_item_ref = pydaw_sequencer_item(
                f_track, a_beat_offset, v.get_length(), v.uid)
            f_sequencer.add_item_ref_by_uid(f_item_ref)
        self.save_region(f_sequencer)

    def get_atm_region(self):
        if os.path.isfile(self.automation_file):
            with open(self.automation_file) as f_file:
                return pydaw_atm_region.from_str(f_file.read())
        else:
            return pydaw_atm_region()

    def save_atm_region(self, a_region):
        self.save_file(pydaw_folder_dawnext, "automation.txt", str(a_region))
        self.commit("Update automation")
        self.IPC.pydaw_save_atm_region()

    def rename_items(self, a_item_names, a_new_item_name):
        """ @a_item_names:  A list of str
        """
        assert isinstance(a_item_names, list), "a_item_names must be a list"
        f_items_dict = self.get_items_dict()
        if len(a_item_names) > 1 or f_items_dict.name_exists(a_new_item_name):
            f_suffix = 1
            f_new_item_name = "{}-".format(a_new_item_name)
            for f_item_name in a_item_names:
                while f_items_dict.name_exists(
                "{}{}".format(f_new_item_name, f_suffix)):
                    f_suffix += 1
                f_items_dict.rename_item(
                    f_item_name, f_new_item_name + str(f_suffix))
        else:
            f_items_dict.rename_item(a_item_names[0], a_new_item_name)
        self.save_items_dict(f_items_dict)

    def set_vol_for_all_audio_items(self, a_uid, a_vol,
                                    a_reverse=None, a_same_vol=False,
                                    a_old_vol=0):
        """ a_uid:  wav_pool uid
            a_vol:  dB
            a_reverse:  None=All, True=reversed-only,
                False=only-if-not-reversed
        """
        f_uid = int(a_uid)
        f_changed_any = False
        assert False, "this needs to be reworked"
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_changed = False
            for f_audio_item in f_audio_region.items.values():
                if f_audio_item.uid == f_uid:
                    if a_reverse is None or \
                    (a_reverse and f_audio_item.reversed) or \
                    (not a_reverse and not f_audio_item.reversed):
                        if not a_same_vol or a_old_vol == f_audio_item.vol:
                            f_audio_item.vol = float(a_vol)
                            f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Changed volume for all audio items "
                "with uid {}".format(f_uid))

    def set_fades_for_all_audio_items(self, a_item):
        """ a_uid:  wav_pool uid
            a_item:  pydaw_audio_item
        """
        f_changed_any = False
        assert False, "this needs to be reworked"
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_changed = False
            for f_audio_item in f_audio_region.items.values():
                if f_audio_item.uid == a_item.uid:
                    if a_item.reversed == f_audio_item.reversed and \
                    a_item.sample_start == f_audio_item.sample_start and \
                    a_item.sample_end == f_audio_item.sample_end:
                        f_audio_item.fade_in = a_item.fade_in
                        f_audio_item.fade_out = a_item.fade_out
                        f_audio_item.fadein_vol = a_item.fadein_vol
                        f_audio_item.fadeout_vol = a_item.fadeout_vol
                        f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Changed volume for all audio items "
                "with uid {}".format(a_item.uid))

    def set_paif_for_all_audio_items(self, a_uid, a_paif):
        """ a_uid:  wav_pool uid
            a_paif:  a list that corresponds to a paif row
        """
        assert False, "this needs to be reworked"
        f_uid = int(a_uid)
        f_changed_any = False
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_paif = self.get_audio_per_item_fx_region(f_region_uid)
            f_changed = False
            for f_index, f_audio_item in f_audio_region.items.items():
                if f_audio_item.uid == f_uid:
                    f_paif.set_row(f_index, a_paif)
                    self.save_audio_per_item_fx_region(f_region_uid, f_paif)
                    self.IPC.pydaw_audio_per_item_fx_region(
                        f_region_uid)
                    f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Update per-audio-item-fx for all audio "
                "items with uid {}".format(f_uid))

    def get_item_string(self, a_item_uid):
        try:
            f_file = open(
                os.path.join(
                    *(str(x) for x in (self.items_folder, a_item_uid))))
        except:
            return ""
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_item_by_uid(self, a_item_uid):
        a_item_uid = int(a_item_uid)
        f_result = pydaw_item.from_str(
            self.get_item_string(a_item_uid), a_item_uid)
        assert f_result.uid == a_item_uid, "UIDs do not match"
        return f_result

    def get_item_by_name(self, a_item_name):
        f_items_dict = self.get_items_dict()
        f_uid = f_items_dict.get_uid_by_name(a_item_name)
        return pydaw_item.from_str(self.get_item_string(f_uid), f_uid)

    def save_audio_inputs(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pyinput, str(a_tracks))

    def get_audio_inputs(self):
        if os.path.isfile(self.audio_inputs_file):
            with open(self.audio_inputs_file) as f_file:
                f_str = f_file.read()
            return libmk.mk_project.AudioInputTracks.from_str(f_str)
        else:
            return libmk.mk_project.AudioInputTracks()

    def save_recorded_items(
            self, a_item_name, a_mrec_list, a_overdub,
            a_sr, a_start_beat, a_end_beat, a_audio_inputs,
            a_sample_count, a_file_name):
        print("\n".join(a_mrec_list))

        f_audio_files_dict = {}

        for f_i, f_ai in zip(range(len(a_audio_inputs)), a_audio_inputs):
            f_val = f_ai.get_value()
            if f_val.rec:
                f_path = os.path.join(
                    libmk.PROJECT.audio_tmp_folder, "{}.wav".format(f_i))
                if os.path.isfile(f_path):
                    f_file_name = "-".join(
                        str(x) for x in (a_file_name, f_i, f_ai.get_name()))
                    f_new_path = os.path.join(
                        libmk.PROJECT.audio_rec_folder, f_file_name)
                    if f_new_path.lower().endswith(".wav"):
                        f_new_path = f_new_path[:-4]
                    if os.path.exists(f_new_path + ".wav"):
                        for f_i in range(10000):
                            f_tmp = "{}-{}.wav".format(f_new_path, f_i)
                            if not os.path.exists(f_tmp):
                                f_new_path = f_tmp
                                break
                    else:
                        f_new_path += ".wav"
                    shutil.move(f_path, f_new_path)
                    f_uid = libmk.PROJECT.get_wav_uid_by_name(f_new_path)
                    sg = libmk.PROJECT.get_sample_graph_by_uid(f_uid)

                    f_audio_files_dict[f_i] = (
                        f_new_path, f_uid, sg.frame_count,
                        f_val.output, f_val.sidechain)
                else:
                    print("Error, path did not exist: {}".format(f_path))

        f_audio_frame = 0

        f_mrec_items = [x.split("|") for x in a_mrec_list]
        f_mrec_items.sort(key=lambda x: int(x[-1]))
        print("\n".join(str(x) for x in f_mrec_items))
        f_item_length = a_end_beat - a_start_beat
        f_sequencer = self.get_region()
        f_note_tracker = {}
        f_items_to_save = {}
        self.rec_item = None
        f_item_name = str(a_item_name)
        f_items_dict = self.get_items_dict()
        f_orig_items = {}
        self.rec_take = {}

        f_audio_tracks = [x[3] for x in f_audio_files_dict.values()]
        f_midi_tracks = [int(x[2]) for x in f_mrec_items]
        f_active_tracks = set(f_audio_tracks + f_midi_tracks)

        f_sequencer.clear_range(f_active_tracks, a_start_beat, a_end_beat)

        def get_item(a_track_num):
            if a_track_num in f_orig_items:
                return f_orig_items[a_track_num].item_uid
            return None

        def new_take():
            self.rec_take = {}
            for f_track in f_active_tracks:
                copy_take(f_track)
            for k, v in f_audio_files_dict.items():
                f_path, f_uid, f_frames, f_output, f_mode = v
                f_item = self.rec_take[f_output]
                f_lane = f_item.get_next_lane()
                f_start = (f_audio_frame / f_frames) * 1000.0
                f_end = 1000.0
                #(f_audio_frame / (f_frames + a_sample_count)) * 1000.0
                f_start = pydaw_util.pydaw_clip_value(f_start, 0.0, f_end)
                f_end = pydaw_util.pydaw_clip_value(f_end, f_start, 1000.0)
                f_audio_item = pydaw_audio_item(
                    f_uid, a_sample_start=f_start, a_sample_end=f_end,
                    a_output_track=f_mode, a_lane_num=f_lane)
                f_index = f_item.get_next_index()
                f_item.add_item(f_index, f_audio_item)

        def copy_take(a_track_num):
            if a_overdub:
                copy_item(a_track_num)
            else:
                new_item(a_track_num)

        def new_item(a_track_num):
            f_name = self.get_next_default_item_name(f_item_name)
            f_uid = self.create_empty_item(f_name)
            f_item = self.get_item_by_uid(f_uid)
            f_items_to_save[f_uid] = f_item
            self.rec_take[a_track_num] = f_item
            f_item_ref = pydaw_sequencer_item(
                a_track_num, a_start_beat, f_item_length, f_uid)
            f_sequencer.add_item_ref_by_uid(f_item_ref)

        def copy_item(a_track_num):
            f_uid = get_item(a_track_num)
            if f_uid is not None:
                f_old_name = f_items_dict.get_name_by_uid(f_uid)
                f_name = self.get_next_default_item_name(
                    f_item_name)
                f_uid = self.copy_item(f_old_name, f_name)
                f_item = self.get_item_by_uid(f_uid)
                f_items_to_save[f_uid] = f_item
                self.rec_take[a_track_num] = f_item
                f_item_ref = pydaw_sequencer_item(
                    a_track_num, a_start_beat, f_item_length, f_uid)
                f_sequencer.add_item_ref_by_uid(f_item_ref)
            else:
                new_item(a_track_num)

        def set_note_length(a_track_num, f_note_num, f_end_beat, f_tick):
            f_note = f_note_tracker[a_track_num][f_note_num]
            f_length = f_end_beat - f_note.start
            if f_length > 0.0:
                f_note.set_length(f_length)
            else:
                assert False, "Need a different algorithm for this"
                print("Using tick length for:")
                f_sample_count = f_tick - f_note.start_sample
                f_seconds = float(f_sample_count) / float(a_sr)
                f_note.set_length(f_seconds * f_beats_per_second)
            print(f_note_tracker[a_track_num].pop(f_note_num))

        new_take()

        for f_event in f_mrec_items:
            f_type, f_beat, f_track = f_event[:3]
            f_track = int(f_track)
            f_beat = float(f_beat)
            if not f_track in f_note_tracker:
                f_note_tracker[f_track] = {}

            f_is_looping = f_type == "loop"

            if f_is_looping:
                new_take()

            if f_type == "loop":
                print("Loop event")
                f_audio_frame += a_sample_count
                continue

            self.rec_item = self.rec_take[f_track]

            if f_type == "on":
                f_note_num, f_velocity, f_tick = (int(x) for x in f_event[3:])
                print("New note: {} {}".format(f_beat, f_note_num))
                f_note = pydaw_note(f_beat, 1.0, f_note_num, f_velocity)
                f_note.start_sample = f_tick
                if f_note_num in f_note_tracker[f_track]:
                    print("Terminating note early: {}".format(
                        (f_track, f_note_num, f_tick)))
                    set_note_length(
                        f_track, f_note_num, f_beat, f_tick)
                f_note_tracker[f_track][f_note_num] = f_note
                self.rec_item.add_note(f_note, a_check=False)
            elif f_type == "off":
                f_note_num, f_tick = (int(x) for x in f_event[3:])
                if f_note_num in f_note_tracker[f_track]:
                    set_note_length(
                        f_track, f_note_num, f_beat, f_tick)
                else:
                    print("Error:  note event not in note tracker")
            elif f_type == "cc":
                f_port, f_val, f_tick = f_event[3:]
                f_port = int(f_port)
                f_val = float(f_val)
                f_cc = pydaw_cc(f_beat, f_port, f_val)
                self.rec_item.add_cc(f_cc)
            elif f_type == "pb":
                f_val = float(f_event[3]) / 8192.0
                f_val = pydaw_util.pydaw_clip_value(f_val, -1.0, 1.0)
                f_pb = pydaw_pitchbend(f_beat, f_val)
                self.rec_item.add_pb(f_pb)
            else:
                print("Invalid mrec event type {}".format(f_type))

        for f_uid, f_item in f_items_to_save.items():
            f_item.fix_overlaps()
            self.save_item_by_uid(f_uid, f_item, a_new_item=True)

        self.save_region(f_sequencer)
        self.commit("Record")

    def reorder_tracks(self, a_dict):
        libmk.IPC.pause_engine()
        f_tracks = self.get_tracks()
        f_tracks.reorder(a_dict)

        f_audio_inputs = self.get_audio_inputs()
        f_audio_inputs.reorder(a_dict)

        f_midi_routings = self.get_midi_routing()
        f_midi_routings.reorder(a_dict)

        f_track_plugins = {k:self.get_track_plugins(k)
            for k in f_tracks.tracks}
        # Delete the existing track files
        for k in f_track_plugins:
            f_path = os.path.join(
                *(str(x) for x in (self.track_pool_folder, k)))
            if os.path.exists(f_path):
                os.remove(f_path)
        for k, v in f_track_plugins.items():
            if v:
                self.save_track_plugins(a_dict[k], v)

        f_graph = self.get_routing_graph()
        f_graph.reorder(a_dict)

        f_region = self.get_region()
        f_region.reorder(a_dict)

        self.save_tracks(f_tracks)
        self.save_audio_inputs(f_audio_inputs)
        self.save_routing_graph(f_graph, a_notify=False)
        self.save_region(f_region, a_notify=False)
        self.save_midi_routing(f_midi_routings, a_notify=False)

        self.IPC.pydaw_open_song(self.project_folder, False)
        libmk.IPC.resume_engine()
        self.commit("Re-order tracks", a_discard=True)
        self.clear_history()

    def get_tracks_string(self):
        try:
            f_file = open(
                os.path.join(self.project_folder, pydaw_file_pytracks))
        except:
            return pydaw_terminating_char
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_tracks(self):
        return pydaw_tracks.from_str(self.get_tracks_string())

    def get_track_plugin_uids(self, a_track_num):
        f_plugins = self.get_track_plugins(a_track_num)
        if f_plugins:
            return set(x.plugin_uid for x in f_plugins.plugins)
        else:
            return f_plugins

    def create_empty_item(self, a_item_name="item"):
        f_items_dict = self.get_items_dict()
        f_item_name = self.get_next_default_item_name(
            a_item_name, a_items_dict=f_items_dict)
        f_uid = f_items_dict.add_new_item(f_item_name)
        self.save_file(pydaw_folder_items, str(f_uid), pydaw_item(f_uid))
        self.IPC.pydaw_save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def copy_item(self, a_old_item, a_new_item):
        f_items_dict = self.get_items_dict()
        f_uid = f_items_dict.add_new_item(a_new_item)
        f_old_uid = f_items_dict.get_uid_by_name(a_old_item)
        f_new_item = self.get_item_by_uid(f_old_uid)
        f_new_item.uid = f_uid
        self.save_file(
            pydaw_folder_items, str(f_uid), str(f_new_item))
        self.IPC.pydaw_save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def save_item(self, a_name, a_item):
        if not self.suppress_updates:
            f_items_dict = self.get_items_dict()
            f_uid = f_items_dict.get_uid_by_name(a_name)
            assert f_uid == a_item.uid, "UIDs do not match"
            self.save_item_by_uid(f_uid, a_item)

    def clear_caches(self):
        self.pixmap_cache_unscaled = {}
        self.painter_path_cache = {}

    def get_item_path(self, a_uid, a_px_per_beat, a_height, a_tempo):
        a_uid = int(a_uid)
        f_key = (a_px_per_beat, a_height, round(a_tempo, 1))
        if a_uid in self.painter_path_cache and \
        f_key in self.painter_path_cache[a_uid]:
            return self.painter_path_cache[a_uid][f_key]
        else:
            if a_uid not in self.pixmap_cache_unscaled:
                f_item_obj = self.get_item_by_uid(a_uid)
                f_path = f_item_obj.painter_path(
                    PIXMAP_BEAT_WIDTH, PIXMAP_TILE_HEIGHT, a_tempo)
                self.pixmap_cache_unscaled[a_uid] = f_path
            if a_uid not in self.painter_path_cache:
                self.painter_path_cache[a_uid] = {}
            f_x, f_y = pydaw_util.scale_sizes(
                PIXMAP_BEAT_WIDTH, PIXMAP_TILE_HEIGHT,
                a_px_per_beat, a_height)
            f_transform = QTransform()
            f_transform.scale(f_x, f_y)
            self.painter_path_cache[a_uid][f_key] = (
                self.pixmap_cache_unscaled[a_uid], f_transform, f_x, f_y)
            return self.painter_path_cache[a_uid][f_key]

    def save_item_by_uid(self, a_uid, a_item, a_new_item=False):
        a_uid = int(a_uid)
        if a_uid in self.painter_path_cache:
            self.painter_path_cache.pop(a_uid)
        if a_uid in self.pixmap_cache_unscaled:
            self.pixmap_cache_unscaled.pop(a_uid)
        if not self.suppress_updates:
            self.save_file(
                pydaw_folder_items, str(a_uid), str(a_item), a_new_item)
            self.IPC.pydaw_save_item(a_uid)

    def save_region(self, a_region, a_notify=True):
        if not self.suppress_updates:
            a_region.fix_overlaps()
            self.save_file("", FILE_SEQUENCER, str(a_region))
            if a_notify:
                self.IPC.pydaw_save_region()
            self.check_output()

    def save_tracks(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pytracks, str(a_tracks))
            #Is there a need for a configure message here?

    def save_track_plugins(self, a_uid, a_track):
        """ @a_uid:   int, the track number
            @a_track: libmk.pydaw_track_plugins
        """
        int(a_uid)  # Test that it can be cast to an int
        f_folder = pydaw_folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def item_exists(self, a_item_name, a_name_dict=None):
        if a_name_dict is None:
            f_name_dict = self.get_items_dict()
        else:
            f_name_dict = a_name_dict
        if str(a_item_name) in f_name_dict.uid_lookup:
            return True
        else:
            return False

    def get_next_default_item_name(
            self, a_item_name="item", a_items_dict=None):
        f_item_name = str(a_item_name)
        f_end_number = re.search(r"[0-9]+$", f_item_name)
        if f_item_name == "item":
            f_start = self.last_item_number
        else:
            if f_end_number:
                f_num_str = f_end_number.group()
                f_start = int(f_num_str)
                f_item_name = f_item_name[:-len(f_num_str)]
                f_item_name = f_item_name.strip('-')
            else:
                f_start = 1
        if a_items_dict:
            f_items_dict = a_items_dict
        else:
            f_items_dict = self.get_items_dict()
        for i in range(f_start, 10000):
            f_result = "{}-{}".format(f_item_name, i)
            if not f_result in f_items_dict.uid_lookup:
                if f_item_name == "item":
                    self.last_item_number = i
                return f_result

    def get_item_list(self):
        f_result = self.get_items_dict()
        return sorted(f_result.uid_lookup.keys())

    def error_log_write(self, a_message):
        f_file = open(os.path.join(self.project_folder, "error.log"), "a")
        f_file.write(a_message)
        f_file.close()

    def check_audio_files(self):
        """ Verify that all audio files exist  """
        f_result = []
        f_regions = self.get_regions_dict()
        f_wav_pool = self.get_wavs_dict()
        f_to_delete = []
        f_commit = False
        for k, v in list(f_wav_pool.name_lookup.items()):
            if not os.path.isfile(v):
                f_to_delete.append(k)
        if len(f_to_delete) > 0:
            f_commit = True
            for f_key in f_to_delete:
                f_wav_pool.name_lookup.pop(f_key)
            self.save_wavs_dict(f_wav_pool)
            self.error_log_write("Removed missing audio item(s) from wav_pool")
        for f_uid in list(f_regions.uid_lookup.values()):
            f_to_delete = []
            f_region = self.get_audio_region(f_uid)
            for k, v in list(f_region.items.items()):
                if not f_wav_pool.uid_exists(v.uid):
                    f_to_delete.append(k)
            if len(f_to_delete) > 0:
                f_commit = True
                for f_key in f_to_delete:
                    f_region.remove_item(f_key)
                f_result += f_to_delete
                self.save_audio_region(f_uid, f_region)
                self.error_log_write("Removed missing audio item(s) "
                    "from region {}".format(f_uid))
        if f_commit:
            self.commit("")
        return f_result

class pydaw_sequencer_item:
    def __init__(
            self, a_track_num, a_start_beat, a_length_beats,
            a_item_uid=-1, a_start_pos=0.0, modified=True):
        self.track_num = int(a_track_num)
        self.start_beat = float(a_start_beat)
        self.length_beats = float(a_length_beats)
        self.item_uid = int(a_item_uid)
        self.start_offset = float(a_start_pos)
        #self.sample_start = float(a_start_pos)
        self.modified = modified

    def clone(self):
        f_self = str(self).split("|")
        return pydaw_sequencer_item(*f_self)

    def __str__(self):
        assert self.item_uid >= 0, "Negative UID"
        return "|".join(str(x) for x in
            (self.track_num, round(self.start_beat, 6),
            round(self.length_beats, 6), self.item_uid,
            round(self.start_offset, 6)))

    def __lt__(self, other):
        if self.track_num == other.track_num:
            return ((self.start_beat < other.start_beat) or
                (self.start_beat == other.start_beat and not self.modified))
        else:
            return self.track_num < other.track_num

class pydaw_abstract_marker:
    def __lt__(self, other):
        if self.beat == other.beat:
            return self.type < other.type
        else:
            return self.beat < other.beat

class pydaw_sequencer_marker(pydaw_abstract_marker):
    def __init__(self, a_beat, a_text):
        self.type = 3
        self.beat = int(a_beat)
        self.text = str(a_text)

    def __str__(self):
        return "|".join(str(x) for x in
            ("E", self.type, self.beat, self.text))

    @staticmethod
    def from_str(self, a_str):
        return pydaw_sequencer_marker(*a_str.split("|", 1))

class pydaw_tempo_marker(pydaw_abstract_marker):
    def __init__(self, a_beat, a_tempo, a_tsig_num, a_tsig_den):
        self.type = 2
        self.beat = int(a_beat)
        self.tempo = round(float(a_tempo), 1)
        self.tsig_num = int(a_tsig_num)
        self.tsig_den = int(a_tsig_den)
        self.real_tempo = (float(a_tsig_den) / 4.0) * self.tempo

    def __str__(self):
        return "|".join(str(x) for x in (
            "E", self.type, self.beat, self.tempo,
            self.tsig_num, self.tsig_den))

    @staticmethod
    def from_str(self, a_str):
        return pydaw_sequencer_marker(*a_str.split("|"))

class pydaw_loop_marker(pydaw_abstract_marker):
    def __init__(self, a_beat, a_start_beat):
        self.type = 1
        self.beat = int(a_beat)
        self.start_beat = int(a_start_beat)

    def __str__(self):
        return "|".join(str(x) for x in
            ("E", self.type, self.beat, self.start_beat))

    @staticmethod
    def from_str(self, a_str):
        return pydaw_sequencer_marker(*a_str.split("|", 1))

class pydaw_sequencer:
    def __init__(self):
        self.items = []
        self.markers = {}
        self.loop_marker = None
        self.set_marker(pydaw_tempo_marker(0, 128.0, 4, 4))

    def set_marker(self, a_marker):
        self.markers[(a_marker.beat, a_marker.type)] = a_marker

    def delete_marker(self, a_marker):
        f_tuple = (a_marker.beat, a_marker.type)
        if f_tuple == (0, 2):
            return # don't delete the first tempo marker
        if f_tuple in self.markers:
            self.markers.pop(f_tuple)

    def has_marker(self, a_beat, a_type):
        f_tuple = tuple(int(x) for x in (a_beat, a_type))
        f_result = [v for k, v in self.markers.items() if k == f_tuple]
        assert len(f_result) <= 1, "Should only be 1 or 0 results"
        return f_result[0] if f_result else None

    def get_markers(self):
        f_tempo_markers = self.get_tempo_markers()
        for f_t1, f_t2 in zip(f_tempo_markers, f_tempo_markers[1:]):
            f_t1.length = f_t2.beat - f_t1.beat
        f_tempo_markers[-1].length = \
            self.get_length() - f_tempo_markers[-1].beat
        return sorted(self.markers.values())

    def set_loop_marker(self, a_marker=None):
        if self.loop_marker:
            self.delete_marker(self.loop_marker)
        if a_marker:
            self.set_marker(a_marker)
        self.loop_marker = a_marker

    def get_tempo_markers(self):
        return sorted(x for x in self.markers.values() if x.type == 2)

    def get_tempo_at_pos(self, a_beat):
        f_tempo_markers = self.get_tempo_markers()
        for f_t1, f_t2 in zip(f_tempo_markers, f_tempo_markers[1:]):
            if a_beat < f_t2.beat and a_beat > f_t1.beat:
                return f_t1.real_tempo
        return f_tempo_markers[-1].real_tempo

    def get_tsig_at_pos(self, a_beat):
        f_tempo_markers = self.get_tempo_markers()
        for f_t1, f_t2 in zip(f_tempo_markers, f_tempo_markers[1:]):
            if a_beat < f_t2.beat and a_beat > f_t1.beat:
                return f_t1.tsig_num
        return f_tempo_markers[-1].tsig_num

    def get_seconds_at_beat(self, a_beat):
        if not a_beat:
            return 0.0
        f_time = 0.0
        f_found = False
        f_tempo_markers = self.get_tempo_markers()
        for f_t1, f_t2 in zip(f_tempo_markers, f_tempo_markers[1:]):
            if a_beat < f_t2.beat and a_beat > f_t1.beat:
                f_time += (a_beat - f_t1.beat) * (60.0 / f_t1.real_tempo)
                f_found = True
                break
            else:
                f_time += (f_t2.beat - f_t1.beat) * (60.0 / f_t1.real_tempo)
        if not f_found:
            f_t1 = f_tempo_markers[-1]
            f_time += (a_beat - f_t1.beat) * (60.0 / f_t1.real_tempo)
        return f_time

    def get_time_at_beat(self, a_beat):
        f_time = self.get_seconds_at_beat(a_beat)
        f_minutes = int(f_time / 60)
        f_seconds = str(round(f_time % 60, 1))
        f_seconds, f_frac = f_seconds.split('.', 1)
        return "{}:{}.{}".format(f_minutes, str(f_seconds).zfill(2), f_frac)

    def get_sample_count(self, a_beat1, a_beat2, a_sr):
        f_time1 = self.get_seconds_at_beat(a_beat1)
        f_time2 = self.get_seconds_at_beat(a_beat2)
        return int(round((f_time1 - f_time2) * a_sr))

    def reorder(self, a_dict):
        for f_item in self.items:
            f_item.track_num = a_dict[f_item.track_num]

    def add_item_ref_by_name(self, a_item_ref, a_item_name, a_uid_dict):
        a_item_ref.item_uid = a_uid_dict.get_uid_by_name(a_item_name)
        self.add_item_ref_by_uid(a_item_ref)

    def add_item_ref_by_uid(self, a_item_ref):
        self.remove_item_ref(a_item_ref)
        self.items.append(a_item_ref)

    def add_item(self, a_item):
        self.items.append(a_item)

    def remove_item_ref(self, a_item):
        f_to_remove = str(a_item)
        for f_item in self.items:
            if str(f_item) == f_to_remove:
                self.items.remove(f_item)

    def split(self, a_points, a_tracks=None, a_modify=True):
        if a_points[0] != 0.0:
            a_points.insert(0, 0.0)
        assert sorted(a_points) == a_points
        f_result = []
        if not a_tracks:
            f_items = self.items[:]
        else:
            f_items = [x for x in self.items if x.track_num in a_tracks]
            if a_port is not None:
                f_items = [x for x in f_items if x.port == a_port]
        for f_p1, f_p2 in zip(a_points, a_points[1:]):
            f_list = [x for x in f_items
                if x.start_beat >= f_p1 and x.start_beat < f_p2]
            f_result.append(f_list)
            for f_item in f_list:
                if f_item.length_beats + f_item.start_beat > f_p2:
                    f_new_item = f_item.clone()
                    f_items.append(f_new_item)
                    f_diff = f_p2 - f_item.start_beat
                    f_new_item.length_beats = f_item.length_beats - f_diff
                    f_new_item.start_offset += f_diff
                    if a_modify:
                        f_item.length_beats = f_diff
        f_list = [x for x in f_items if x > a_points[-1]]
        f_result.append(f_list)
        return f_result

    def insert_space(self, a_start, a_length):
        for f_item in (x for x in self.items if x.start_beat >= a_start):
            f_item.start_beat += a_length

    def clear_range(self, a_track_list, a_start_beat, a_end_beat):
        for f_item in [x for x in self.items if x.track_num in a_track_list]:
            f_end_beat = f_item.start_beat + f_item.length_beats
            if f_item.start_beat >= a_start_beat and \
            a_start_beat < a_end_beat:
                if f_end_beat <= a_end_beat:
                    self.items.remove(f_item)
                else:
                    f_diff = a_end_beat - f_item.start_beat
                    f_item.start_offset += f_diff
                    f_item.length_beats -= f_diff
                    f_item.start_beat = a_end_beat
            elif f_item.start_beat < a_start_beat:
                if f_end_beat >= a_start_beat and \
                f_end_beat < a_end_beat:
                    f_item.length_beats = a_start_beat - f_item.start_beat

    def get_length(self):
        f_item_max = max(x.start_beat + x.length_beats
            for x in self.items) if self.items else 0
        f_marker_max = max(
            x.beat for x in self.markers.values()) if self.markers else 0
        return max((f_item_max, f_marker_max)) + 64

    def fix_overlaps(self):
        # Delete items with length < 1/16th note
        f_to_delete = {x for x in self.items if x.length_beats < 0.25}
        for f_i in range(TRACK_COUNT_ALL):
            f_items = [
                x for x in self.items if x.track_num == f_i and
                x not in f_to_delete]
            if f_items:
                f_items.sort()
                for f_item, f_next in zip(f_items, f_items[1:]):
                    if f_item.start_beat == f_next.start_beat:
                        # sort is by start_beat then (not modified)
                        f_to_delete.add(f_item)
                    f_end = f_item.start_beat + f_item.length_beats
                    if f_end > f_next.start_beat:
                        f_item.length_beats = (
                            f_next.start_beat - f_item.start_beat)
                        if f_item.length_beats < 0.25:
                            f_to_delete.add(f_item)
        for f_item in f_to_delete:
            self.items.remove(f_item)


    def __str__(self):
        f_result = []
        f_result.append("M|{}".format(
            len([x for x in self.markers.values() if x.type in (1, 2)])))
        for v in sorted(self.markers.values()):
            f_result.append(str(v))
        for f_i in range(TRACK_COUNT_ALL):
            f_items = [x for x in self.items if x.track_num == f_i]
            if f_items:
                f_items.sort()
                f_result.append("C|{}|{}".format(f_i, len(f_items)))
                for f_item in f_items:
                    f_result.append(str(f_item))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_sequencer()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            else:
                f_item_arr = f_line.split("|")
                if f_item_arr[0] == "E":
                    f_type = int(f_item_arr[1])
                    if f_type == 1:
                        f_result.set_loop_marker(
                            pydaw_loop_marker(*f_item_arr[2:]))
                    elif f_type == 2:
                        f_result.set_marker(
                            pydaw_tempo_marker(*f_item_arr[2:]))
                    elif f_type == 3:
                        f_result.set_marker(
                            pydaw_sequencer_marker(*f_item_arr[2:]))
                    else:
                        assert False, "Invalid type {}".format(f_type)
                    continue
                if f_item_arr[0] == "M":
                    continue
                if f_item_arr[0] == "C":
                    continue
                f_result.add_item(
                    pydaw_sequencer_item(*f_item_arr, modified=False))
        f_result.items.sort()
        return f_result


class pydaw_atm_region:
    def __init__(self):
        self.plugins = {}
        self.points = []

    def split(self, a_points, a_plugins=None, a_port=None):
        if a_points[0] != 0.0:
            a_points.insert(0, 0.0)
        assert(sorted(a_points) == a_points)
        f_result = []
        if not a_plugins:
            f_points = self.points[:]
        else:
            f_points = [x for x in self.points if x.index in a_plugins]
            if a_port is not None:
                f_points = [x for x in f_points if x.port == a_port]
        for f_p1, f_p2 in zip(a_points, a_points[1:]):
            f_list = [x for x in f_points if x >= f_p1 and x < f_p2]
            f_result.append(f_list)
        f_list = [x for x in f_points if x > a_points[-1]]
        f_result.append(f_list)
        return f_result

    def copy_range_all(self, a_start, a_end):
        return [x.clone() for x in self.points
            if x.beat >= a_start and x.beat < a_end]

    def copy_range_by_plugins(self, a_start, a_end, a_plugins):
        f_result = [x.clone() for x in self.points
            if x.beat >= a_start and x.beat < a_end and x.index in a_plugins]
        for x in f_result:
            x.beat -= a_start
        return f_result

    def add_port_list(self, a_point):
        if not a_point.index in self.plugins:
            self.plugins[a_point.index] = {}
        if not a_point.port_num in self.plugins[a_point.index]:
            self.plugins[a_point.index][a_point.port_num] = []

    def add_point(self, a_point):
        self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].append(a_point)
        self.points.append(a_point)

    def remove_point(self, a_point):
        #self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].remove(a_point)
        self.points.remove(a_point)

    def get_ports(self, a_index):
        a_index = int(a_index)
        if a_index not in self.plugins:
            return []
        else:
            return sorted(self.plugins[a_index])

    def get_points(self, a_index, a_port_num):
        a_port_num = int(a_port_num)
        a_index = int(a_index)
        if a_index not in self.plugins or \
        a_port_num not in self.plugins[a_index]:
            return []
        else:
            f_result = self.plugins[a_index][a_port_num]
            f_result.sort()
            return f_result

    def clear_range_by_plugins(self, a_start, a_end, a_plugins):
        f_result = [x for x in self.points
            if x.beat >= a_start and x.beat < a_end and x.index in a_plugins]
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_plugins(self, a_plugin_uids):
        f_result = [x for x in self.points if x.index in a_plugin_uids]
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_port(self, a_index, a_port_num):
        f_result = self.get_points(a_index, a_port_num)
        for f_point in f_result:
            self.remove_point(f_point)

    def clear_range(self, a_index, a_port_num, a_start_beat, a_end_beat):
        f_list = self.get_points(a_index, a_port_num)
        if f_list:
            f_new = [x for x in f_list if
                x.beat < a_start_beat or x.beat >= a_end_beat]
            f_result = [x for x in f_list if
                x.beat >= a_start_beat or x.beat < a_end_beat]
            self.plugins[a_index][a_port_num] = f_new
            return f_result

    def smooth_points(
            self, a_index, a_port_num, a_plugin_index, a_points, a_linear):
        """ The new points are appended to a_points so that they can be
            re-selected in the sequencer
        """
        if len(a_points) <= 1:
            return
        a_points.sort()
        f_start = a_points[0]
        f_end = a_points[-1]
        self.clear_range(a_index, a_port_num, f_start.beat, f_end.beat)
        f_inc = 0.0625 # 64th note
        f_result = self.plugins[a_index][a_port_num]
        f_smoother = pydaw_util.OnePoleLP(f_start.cc_val)
        for f_point, f_next in zip(a_points, a_points[1:]):
            f_beat = f_point.beat + f_inc
            f_val = f_point.cc_val
            f_beat_next = f_next.beat
            f_val_next = f_next.cc_val
            f_result.append(f_point)
            if round(f_val, 3) == round(f_val_next, 3):
                continue
            f_beat_diff = f_beat_next - f_beat
            if f_beat_diff < f_inc:
                f_result.append(f_point)
                continue
            f_inc_count = int(round(f_beat_diff / f_inc))
            for f_i in range(1, f_inc_count + 1):
                if a_linear:
                    f_int_val = pydaw_util.linear_interpolate(
                        f_val, f_val_next, (f_i / f_inc_count))
                else:
                    f_int_val = pydaw_util.cosine_interpolate(
                        f_val, f_val_next, (f_i / f_inc_count))
                f_int_val = f_smoother.process(f_int_val)
                f_point2 = pydaw_atm_point(
                    f_beat, a_port_num, f_int_val, a_index, a_plugin_index)
                f_result.append(f_point2)
                a_points.append(f_point2)
                f_beat += f_inc
        f_result.append(f_end)

    def __str__(self):
        # New file format:
        # lines starting with 'p':  p|plugin_uid|port_count
        # lines starting with 'q':  n|port_num|point_count
        # other lines:  pydaw_atm_point
        f_result = []
        for f_index in sorted(self.plugins):
            port_dict = {k:v for k, v in self.plugins[f_index].items() if v}
            if not port_dict:
                continue
            port_len = len(port_dict)
            f_result.append(
                "|".join(str(x) for x in
                ("p", f_index, port_len)))
            for port_num in sorted(port_dict):
                port_list = port_dict[port_num]
                port_list.sort()
                f_result.append(
                    "|".join(str(x) for x in
                    ("q", port_num, len(port_list))))
                for f_point in port_list:
                    f_result.append(str(f_point))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_atm_region()
        for f_line in str(a_str).split("\n"):
            if f_line == pydaw_terminating_char:
                break
            if f_line[0] in ("p", "q"):
                continue
            f_point = pydaw_atm_point.from_str(f_line)
            f_result.add_point(f_point)
        return f_result

class pydaw_atm_point:
    def __init__(
            self, a_beat, a_port_num, a_cc_val, a_index, a_plugin_index,
            a_break_after=0, a_curve=0.0):
        self.beat = round(float(a_beat), 4)
        self.port_num = int(a_port_num)
        self.cc_val = round(float(a_cc_val), 4)
        self.index = int(a_index) # Now means plugin pool UID
        self.plugin_index = int(a_plugin_index) # UID of the plugin
        self.break_after = int(a_break_after)
        assert self.break_after in (0, 1), str(a_break_after)
        # Doesn't do anything yet, just adding it to the file format now
        # so I don't have to code around it later
        self.curve = float(a_curve)

    def set_val(self, a_val):
        self.cc_val = pydaw_clip_value(float(a_val), 0.0, 127.0, True)

    def __lt__(self, other):
        return self.beat < other.beat

#    def __eq__(self, other):
#        return (
#            (self.track == other.track) and
#            (self.beat == other.beat) and
#            (self.port_num == other.port_num) and
#            (self.cc_val == other.cc_val) and
#            (self.index == other.index) and
#            (self.plugin_index == other.plugin_index))

    def __str__(self):
        return "|".join(str(x) for x in (
            self.beat, self.port_num, self.cc_val,
            self.index, self.plugin_index, self.break_after, self.curve))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_atm_point(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_atm_point.from_arr(f_arr)

    def clone(self):
        return pydaw_atm_point.from_str(str(self))


class pydaw_item:
    def __init__(self, a_uid):
        self.items = {}  # audio items:  TODO rename
        self.notes = []
        self.ccs = []
        self.pitchbends = []
        self.uid = int(a_uid)
        self.fx_list = {} #per-audio-item-fx

    def get_next_lane(self):
        f_lanes = set(x.lane_num for x in self.items.values())
        for f_i in range(24):
            if f_i not in f_lanes:
                return f_i
        return 0

    def painter_path(self, a_px_per_beat, a_height, a_tempo):
        f_seconds_per_beat = 60.0 / a_tempo
        f_audio_path = QPainterPath()
        f_audio_path.addRect(0, 0, 1, 1)
        for f_item in sorted(
        self.items.values(), key=lambda x: x.start_beat):
            f_graph = libmk.PROJECT.get_sample_graph_by_uid(
                f_item.uid)
            f_width = (f_graph.length_in_seconds /
                f_seconds_per_beat) * a_px_per_beat
            f_paths = f_graph.create_sample_graph(
                True, f_width, a_height, f_item)
            f_y_inc = a_height / len(f_paths)
            f_y_pos = 0.0
            for f_painter_path in f_paths:
                f_painter_path.translate(
                    a_px_per_beat * f_item.start_beat, f_y_pos)
                f_audio_path.addPath(f_painter_path)
                f_y_pos += f_y_inc

        f_notes_path = QPainterPath()
        f_notes_path.addRect(0, 0, 1, 1)
        if self.notes:
            f_note_set = sorted(
                set(x.note_num for x in self.notes), reverse=True)
            f_note_h_area = (a_height * 0.6)
            f_note_height = round(f_note_h_area / len(f_note_set))
            f_note_height = pydaw_util.pydaw_clip_max(
                f_note_height, a_height * 0.1)
            f_min = 1.0 - (min(f_note_set) / 127.0)
            f_note_bias = (f_note_h_area -
                (f_note_height * len(f_note_set))) * f_min
            f_note_dict = {x:((((y * f_note_height) + a_height * 0.36)) +
                    f_note_bias)
                for x, y in zip(f_note_set, range(len(f_note_set)))}
            for f_note in self.notes:
                f_y_pos = f_note_dict[f_note.note_num]
                f_x_pos = f_note.start * a_px_per_beat
                f_width = f_note.length * a_px_per_beat
                f_notes_path.addRect(f_x_pos, f_y_pos, f_width, f_note_height)

        f_audio_width = f_audio_path.boundingRect().width()
        f_notes_width = f_notes_path.boundingRect().width()

        f_width = max(f_audio_width, f_notes_width)

        f_count = int(f_width // PIXMAP_TILE_WIDTH) + 1
        f_result = []

        f_note_brush = QColor.fromRgb(210, 210, 210, 220)
        f_audio_brush = QColor.fromRgb(150, 150, 150, 210)
        f_note_pen = QPen(f_note_brush)
        f_pen = QPen(f_audio_brush)
        f_pen.setCosmetic(True)

        for f_i in range(f_count):
            f_pixmap = QPixmap(min(f_width, PIXMAP_TILE_WIDTH), a_height)
            f_width -= PIXMAP_TILE_WIDTH
            f_pixmap.fill(QtCore.Qt.transparent)
            f_painter = QPainter(f_pixmap)
            f_painter.setRenderHint(QPainter.HighQualityAntialiasing)
            f_painter.setPen(f_pen)
            f_painter.setBrush(f_audio_brush)
            f_painter.drawPath(f_audio_path)
            f_painter.setPen(f_note_pen)
            f_painter.setBrush(f_note_brush)
            f_painter.drawPath(f_notes_path)
            f_painter.end()
            f_result.append(f_pixmap)
            for f_path in (f_notes_path, f_audio_path):
                f_path.translate(-PIXMAP_TILE_WIDTH, 0)
        return f_result

    def get_length(self, a_tempo=None):
        f_result = 0.0

        for f_note in self.notes:
            f_end = f_note.start + f_note.length
            if f_end > f_result:
                f_result = f_end

        for f_ev in self.ccs + self.pitchbends:
            if f_ev.start > f_result:
                f_result = f_ev.start

        if a_tempo:
            f_spb = 60.0 / a_tempo
            for f_item in self.items.values():
                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_item.uid)
                f_end = (f_graph.length_in_seconds / f_spb) + f_item.start_beat
                if f_end > f_result:
                    f_end = f_result

        return f_result

    def confine_audio_items(self, a_ref, a_tempo):
        f_to_delete = []
        f_start = a_ref.start_offset
        f_end = a_ref.length_beats + f_start

        f_spb = 60.0 / a_tempo
        f_min_len = f_spb / 16.0
        for k, v in self.items.items():
            f_item_start = v.start_beat
            if f_item_start > f_end:
                print("Delete after {} {}".format(f_item_start, f_end))
                f_to_delete.append(k)
                continue
            f_graph = libmk.PROJECT.get_sample_graph_by_uid(v.uid)
            f_ss, f_se = (x * 0.001 for x in (v.sample_start, v.sample_end))
            f_diff = f_se - f_ss
            f_end_beat = ((f_graph.length_in_seconds / f_spb) *
                f_diff) + f_item_start
            if f_end_beat < f_start:
                print("Delete before {} {}".format(f_end_beat, f_start))
                f_to_delete.append(k)
                continue
            if f_item_start < f_start:
                f_beat_diff = f_start - f_item_start
                f_seconds = f_spb * f_beat_diff
                f_offset = (f_seconds / f_graph.length_in_seconds) * 1000.0
                v.sample_start += f_offset
                v.start_beat = f_start
                print("LT")
            if f_end_beat > f_end:
                f_beat_diff = f_end_beat - f_end
                f_seconds = f_spb * f_beat_diff
                f_offset = (f_seconds / f_graph.length_in_seconds) * 1000.0
                v.sample_end -= f_offset
                print("GT")
            f_new_length_seconds = ((v.sample_end - v.sample_start) *
                0.001) * f_graph.length_in_seconds
            if f_new_length_seconds < f_min_len:
                print("Popping item of length {}".format(f_new_length_seconds))
                f_to_delete.append(k)
            for f_tuple in locals().items():
                print(f_tuple)
        for k in f_to_delete:
            self.items.pop(k)

    def extend(self, a_new_ref, a_ref, a_item2, a_tempo):
        """ Glue 2 items together, adding f_offset to the
            event positions of a_item2
        """
        f_start_offset = a_ref.start_offset
        f_offset = (a_ref.start_beat - a_new_ref.start_beat -
            a_ref.start_offset)
        f_end_offset = a_ref.start_offset + a_ref.length_beats

        f_notes = [x.clone() for x in a_item2.notes
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_note in f_notes:
            f_note.start += f_offset
            self.add_note(f_note, False)
        self.notes.sort()

        f_ccs = [x.clone() for x in a_item2.ccs
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_cc in f_ccs:
            f_cc.start += f_offset
            self.add_cc(f_cc)
        self.ccs.sort()

        f_pbs = [x.clone() for x in a_item2.pitchbends
            if x.start >= f_start_offset and x.start < f_end_offset]

        for f_pb in f_pbs:
            f_pb.start += f_offset
            self.add_pb(f_pb)
        self.pitchbends.sort()

        a_item2.confine_audio_items(a_ref, a_tempo)
        for k, v in a_item2.items.items():
            f_index = self.get_next_index()
            if f_index == -1:
                print("Exceeded the max audio item count, dropping items")
                break
            v.start_beat += f_offset
            self.add_item(f_index, v)
            if k in a_item2.fx_list:
                self.set_row(f_index, a_item2.fx_list[k])

    #per-audio-item-fx

    def get_row_str(self, a_row_index):
        f_result = str(a_row_index)
        for f_item in self.fx_list[int(a_row_index)]:
            f_result += str(f_item)
        return f_result

    def set_row(self, a_row_index, a_fx_list):
        self.fx_list[int(a_row_index)] = a_fx_list

    def clear_row(self, a_row_index):
        self.fx_list.pop(a_row_index)

    def clear_row_if_exists(self, a_row_index):
        if a_row_index in self.fx_list:
            self.fx_list.pop(a_row_index)

    def get_row(self, a_row_index, a_return_none=False):
        if int(a_row_index) in self.fx_list:
            return self.fx_list[int(a_row_index)]
        else:
            # print("Index {} not found in "
            #     "pydaw_audio_item_fx_region".format(a_row_index))
            if a_return_none:
                return None
            else:
                f_result = []
                for f_i in range(8):
                    f_result.append(pydaw_modulex_settings(64, 64, 64, 0))
                return f_result

    #end per-audio-item-fx

    def add_note(self, a_note, a_check=True):
        if a_check:
            for note in self.notes:
                if note.overlaps(a_note):
                    # TODO:  return -1 instead of True, and the
                    # offending editor_index when False
                    return False
        self.notes.append(a_note)
        self.notes.sort()
        if not a_check:
            self.fix_overlaps()
        return True

    def remove_note(self, a_note):
        try:
            self.notes.remove(a_note)
        except Exception as ex:
            print("\n\n\nException in remove_note:\n{}".format(ex))
            print((repr(traceback.extract_stack())))
            print("\n\n\n")

    def velocity_mod(self, a_amt, a_start_beat=0.0,
                     a_end_beat=4.0, a_line=False,
                     a_end_amt=127, a_add=False, a_notes=None):
        """ velocity_mod
        (self, a_amt, #The amount to add or subtract
         a_start_beat=0.0, #modify values with a start at >= this, and...
         a_end_beat=4.0, # <= to this.
         a_line=False, # draw a line to a_end,
             otherwise all events are modified by a_amt
         a_end_amt=127, #not used unless a_line=True
         a_add=False, #True to add/subtract from each value, False to assign
         a_notes=None) #Process all notes if None, or
             selected if a list of notes is provided

         Modify the velocity of a range of notes
         """
        f_notes = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for f_note in a_notes:
                for f_note2 in self.notes:
                    if f_note2 == f_note:
                        f_notes.append(f_note2)
                        break

        f_range_beats = a_end_beat - a_start_beat

        for note in f_notes:
            if note.start >= a_start_beat and note.start <= a_end_beat:
                if a_line:
                    f_frac = ((note.start - a_start_beat)/f_range_beats)
                    f_value = int(((a_end_amt - a_amt) * f_frac) + a_amt)
                else:
                    f_value = int(a_amt)
                if a_add:
                    note.velocity += f_value
                else:
                    note.velocity = f_value
                if note.velocity > 127:
                    note.velocity = 127
                elif note.velocity < 1:
                    note.velocity = 1

    def quantize(
            self, a_beat_frac, a_events_move_with_item=False,
            a_notes=None, a_selected_only=False):
        f_notes = []
        f_ccs = []
        f_pbs = []

        f_result = []

        if a_notes is None:
            f_notes = self.notes
            f_ccs = self.ccs
            f_pbs = self.pitchbends
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        if a_events_move_with_item:
                            f_start = f_note.start
                            f_end = f_note.start + f_note.length
                            for f_cc in self.ccs:
                                if f_cc.start >= f_start and \
                                f_cc.start <= f_end:
                                    f_ccs.append(f_cc)
                            for f_pb in self.pitchbends:
                                if f_pb.start >= f_start and \
                                f_pb.start <= f_end:
                                    f_pbs.append(f_pb)
                        f_notes.append(f_note)
                        break

        f_quantized_value = bar_frac_text_to_float(a_beat_frac)
        f_quantize_multiple = 1.0 / f_quantized_value

        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            f_new_start = round(note.start *
                f_quantize_multiple) * f_quantized_value
            note.start = f_new_start
            shift_adjust = note.start - f_new_start
            f_new_length = round(note.length *
                f_quantize_multiple) * f_quantized_value
            if f_new_length == 0.0:
                f_new_length = f_quantized_value
            note.set_length(f_new_length)
            f_result.append(str(note))

        self.fix_overlaps()

        if a_events_move_with_item:
            for cc in f_ccs:
                cc.start -= shift_adjust
            for pb in f_pbs:
                pb.start -= shift_adjust

        return f_result

    def transpose(
            self, a_semitones, a_octave=0, a_notes=None,
            a_selected_only=False, a_duplicate=False):
        f_total = a_semitones + (a_octave * 12)
        f_notes = []
        f_result = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        f_notes.append(f_note)
                        break
        if a_duplicate:
            f_duplicates = []
        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            if a_duplicate:
                f_duplicates.append(pydaw_note.from_str(str(note)))
            note.note_num += f_total
            note.note_num = pydaw_clip_value(note.note_num, 0, 120)
            f_result.append(str(note))
        if a_duplicate:
            self.notes += f_duplicates
            self.notes.sort()
        return f_result

    def smooth_automation_points(self, a_is_cc, a_cc_num=-1):
        if a_is_cc:
            f_this_cc_arr = []
            f_result_arr = []
            f_cc_num = int(a_cc_num)
            for f_cc in self.ccs:
                if f_cc.cc_num == f_cc_num:
                    f_new_cc = pydaw_cc(f_cc.start, f_cc_num, f_cc.cc_val)
                    f_this_cc_arr.append(f_new_cc)
            f_this_cc_arr.sort()
            for f_cc1, f_cc2 in zip(f_this_cc_arr, f_this_cc_arr[1:]):
                f_val_diff = abs(f_cc2.cc_val - f_cc1.cc_val)
                if f_val_diff == 0:
                    continue
                f_time_inc = .0625  #1/64th note
                f_start = f_cc1.start + f_time_inc

                f_start_diff = f_cc2.start - f_cc1.start
                if f_start_diff == 0.0:
                    continue

                f_inc = (f_val_diff / (f_start_diff * 16.0))
                if (f_cc1.cc_val) > (f_cc2.cc_val):
                    f_inc *= -1.0
                f_new_val = f_cc1.cc_val + f_inc
                while True:
                    f_interpolated_cc = pydaw_cc(f_start, f_cc_num, f_new_val)
                    f_new_val += f_inc
                    f_result_arr.append(f_interpolated_cc)
                    f_start += f_time_inc
                    if f_start >= (f_cc2.start - 0.0625):
                        break

            self.ccs += f_result_arr
            self.ccs.sort()
        else:
            f_this_pb_arr = []
            f_result_arr = []

            for f_pb in self.pitchbends:
                f_new_pb = pydaw_pitchbend(f_pb.start, f_pb.pb_val)
                f_this_pb_arr.append(f_new_pb)

            for f_pb1, f_pb2 in zip(f_this_pb_arr, f_this_pb_arr[1:]):
                f_val_diff = abs(
                    f_pb2.pb_val - f_pb1.pb_val)
                if f_val_diff == 0.0:
                    continue
                f_time_inc = 0.0625
                f_start = f_pb1.start + f_time_inc
                f_start_diff = f_pb2.start - f_pb1.start
                if f_start_diff == 0.0:
                    continue
                f_val_inc = f_val_diff / (f_start_diff * 16.0)
                if f_pb1.pb_val > f_pb2.pb_val:
                    f_val_inc *= -1.0
                f_new_val = f_pb1.pb_val + f_val_inc

                while True:
                    f_interpolated_pb = pydaw_pitchbend(f_start, f_new_val)
                    f_new_val += f_val_inc
                    f_result_arr.append(f_interpolated_pb)
                    f_start += f_time_inc
                    if f_start >= (f_pb2.start - 0.0625):
                        break
            self.pitchbends += f_result_arr
            self.pitchbends.sort()

    def fix_overlaps(self):
        """ Truncate the lengths of any notes that overlap
            the start of another note
        """
        f_to_delete = []
        for f_note in self.notes:
            if f_note not in f_to_delete:
                for f_note2 in self.notes:
                    if f_note != f_note2 and f_note2 not in f_to_delete:
                        if f_note.note_num == f_note2.note_num:
                            if f_note2.start == f_note.start:
                                if f_note2.length == f_note.length:
                                    f_to_delete.append(f_note2)
                                elif f_note2.length > f_note.length:
                                    f_note2.length = \
                                        f_note2.length - f_note.length
                                    f_note2.start = f_note.end
                                    f_note2.set_end()
                                else:
                                    f_note.length = \
                                        f_note.length - f_note2.length
                                    f_note.start = f_note2.end
                                    f_note.set_end()
                            elif f_note2.start > f_note.start:
                                if f_note.end > f_note2.start:
                                    f_note.length = \
                                        f_note2.start - f_note.start
                                    f_note.set_end()
        for f_note in self.notes:
            if f_note.length < pydaw_min_note_length:
                f_to_delete.append(f_note)
        for f_note in f_to_delete:
            self.notes.remove(f_note)

    def get_next_default_note(self):
        pass

    def add_cc(self, a_cc):
        if a_cc in self.ccs:
            return False
        self.ccs.append(a_cc)
        self.ccs.sort()
        return True

    def remove_cc(self, a_cc):
        self.ccs.remove(a_cc)

    def remove_cc_range(self, a_cc_num, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than a_start_beat
            and less than a_end_beat
        """
        f_ccs_to_delete = []
        for cc in self.ccs:
            if cc.cc_num == a_cc_num and \
            cc.start >= a_start_beat and \
            cc.start <= a_end_beat:
                f_ccs_to_delete.append(cc)
        for cc in f_ccs_to_delete:
            self.remove_cc(cc)

    #TODO:  A maximum number of events per line?
    def draw_cc_line(self, a_cc, a_start, a_start_val,
                     a_end, a_end_val, a_curve=0):
        f_cc = int(a_cc)
        f_start = float(a_start)
        f_start_val = int(a_start_val)
        f_end = float(a_end)
        f_end_val = int(a_end_val)
        #Remove any events that would overlap
        self.remove_cc_range(f_cc, f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -1
        else:
            f_inc = 1
        f_time_inc = abs(f_start_diff / float(f_val_diff))
        for i in range(0, (f_val_diff + 1)):
            self.ccs.append(pydaw_cc(f_start, f_cc, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        self.ccs.sort()

    def add_pb(self, a_pb):
        if a_pb in self.pitchbends:
            return False
        self.pitchbends.append(a_pb)
        self.pitchbends.sort()
        return True

    def remove_pb(self, a_pb):
        self.pitchbends.remove(a_pb)

    def remove_pb_range(self, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than
            a_start_beat and less than a_end_beat
        """
        f_pbs_to_delete = []
        for pb in self.pitchbends:
            if pb.start >= a_start_beat and \
            pb.start <= a_end_beat:
                f_pbs_to_delete.append(pb)
        for pb in f_pbs_to_delete:
            self.remove_pb(pb)

    def draw_pb_line(self, a_start, a_start_val, a_end, a_end_val, a_curve=0):
        f_start = float(a_start)
        f_start_val = float(a_start_val)
        f_end = float(a_end)
        f_end_val = float(a_end_val)
        #Remove any events that would overlap
        self.remove_pb_range(f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -0.025
        else:
            f_inc = 0.025
        f_time_inc = abs(f_start_diff/(float(f_val_diff) * 40.0))
        for i in range(0, int((f_val_diff * 40) + 1)):
            self.pitchbends.append(pydaw_pitchbend(f_start, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        #Ensure that the last value is what the user wanted it to be
        self.pitchbends[(len(self.pitchbends) - 1)].pb_val = f_end_val
        self.pitchbends.sort()

    def get_next_default_cc(self):
        pass

    @staticmethod
    def from_str(a_str, a_uid):
        f_result = pydaw_item(a_uid)
        f_arr = a_str.split("\n")
        for f_event_str in f_arr:
            if f_event_str == pydaw_terminating_char:
                break
            else:
                f_event_arr = f_event_str.split("|")
                if f_event_arr[0] == "n":
                    f_result.add_note(pydaw_note.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "c":
                    f_result.add_cc(pydaw_cc.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "p":
                    f_result.add_pb(pydaw_pitchbend.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "a":
                    f_result.add_item(
                        int(f_event_arr[1]),
                        pydaw_audio_item.from_arr(f_event_arr[2:]))
                elif f_event_arr[0] == "f":
                    f_items_arr = []
                    f_item_index = f_event_arr[1]
                    f_vals_arr = f_event_arr[2:]
                    for f_i in range(8):
                        f_index = f_i * 4
                        f_index_end = f_index + 4
                        a_knob0, a_knob1, a_knob2, a_type = f_vals_arr[
                            f_index:f_index_end]
                        f_items_arr.append(
                            pydaw_modulex_settings(
                                a_knob0, a_knob1, a_knob2, a_type))
                    f_result.set_row(f_item_index, f_items_arr)
                elif f_event_arr[0] == "U":
                    f_result.uid = int(f_event_arr[1])
                elif f_event_arr[0] == "M":
                    pass
                else:
                    print("Error: {}".format(f_event_arr))
                    assert False, "Invalid type '{}'".format(f_event_arr[0])
        return f_result

    def deduplicate(self):
        len_orig = len(self.notes)
        f_note_set = {str(x) for x in self.notes}
        note_diff = len_orig - len(f_note_set)
        if note_diff:
            print("Deduplicated {} notes".format(note_diff))
            self.notes = [pydaw_note.from_str(x) for x in f_note_set]
            self.notes.sort()
        # TODO:  Others

    def __str__(self):
        self.deduplicate()
        f_result = []
        f_result.append("U|{}".format(self.uid))
        f_midi_count = len(self.notes) + len(self.ccs) + len(self.pitchbends)
        f_result.append("M|{}".format(f_midi_count))
        f_result += [str(x) for x in
            sorted(self.notes + self.ccs + self.pitchbends)]
        for k, f_item in list(self.items.items()):
            f_result.append("a|{}|{}".format(k, f_item))
        for k, v in self.fx_list.items():
            f_result.append("f|{}".format(self.get_row_str(k)))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    def reorder(self, a_dict):
        for f_item in self.items.values():
            f_item.output_track = a_dict[f_item.output_track]
            if f_item.send1 != -1:
                f_item.send1 = a_dict[f_item.send1]
            if f_item.send2 != -1:
                f_item.send2 = a_dict[f_item.send2]

    def get_next_index(self):
        """ Return the next available index, or -1
            if none are available
        """
        for i in range(MAX_AUDIO_ITEM_COUNT):
            if not i in self.items:
                return i
        return -1

    def split(self, a_index):
        f_region0 = pydaw_audio_region()
        f_region1 = pydaw_audio_region()
        for k, v in list(self.items.items()):
            if v.start_bar >= a_index:
                v.start_bar -= a_index
                f_region1.items[k] = v
            else:
                f_region0.items[k] = v
        return f_region0, f_region1

    def add_item(self, a_index, a_item):
        self.items[int(a_index)] = a_item

    def remove_item(self, a_index):
        self.items.pop(int(a_index))

    def deduplicate_items(self):
        f_to_delete = []
        f_values = []
        for k, v in list(self.items.items()):
            f_str = str(v)
            if f_str in f_values:
                f_to_delete.append(k)
            else:
                f_values.append(f_str)
        for f_key in f_to_delete:
            print("Removing duplicate audio item at {}".format(f_key))
            self.items.pop(f_key)
            if f_key in self.fx_list:
                self.fx_list.pop(f_key)

    def set_region_length(self, a_length):
        """ Remove any items not within the new length,
            or change any end points that are past
            the new end.  Return True if anything changed, otherwise False
        """
        f_to_delete = []
        f_length = int(a_length)
        for k, v in list(self.items.items()):
            if v.start_bar >= f_length:
                f_to_delete.append(k)
                print("Item begins after new region length of "
                      "{}, deleting: {}".format(a_length, v))
        for f_key in f_to_delete:
            self.items.pop(f_key)


class pydaw_audio_item(MkAudioItem):
    def clip_at_region_end(self, a_region_length, a_tempo,
            a_sample_length_seconds, a_truncate=True):
        f_region_length_beats = a_region_length
        f_seconds_per_beat = (60.0 / a_tempo)
        f_region_length_seconds = f_seconds_per_beat * f_region_length_beats
        f_item_start_beats = self.start_beat
        f_item_start_seconds = f_item_start_beats * f_seconds_per_beat
        f_sample_start_seconds = (
            self.sample_start * 0.001 * a_sample_length_seconds)
        f_sample_end_seconds = (
            self.sample_end * 0.001 * a_sample_length_seconds)
        f_actual_sample_length = f_sample_end_seconds - f_sample_start_seconds
        f_actual_item_end = f_item_start_seconds + f_actual_sample_length

        if a_truncate and f_actual_item_end > f_region_length_seconds:
            f_new_item_end_seconds = (f_region_length_seconds -
                f_item_start_seconds) + f_sample_start_seconds
            f_new_item_end = (
                f_new_item_end_seconds / a_sample_length_seconds) * 1000.0
            print("clip_at_region_end:  new end: {}".format(f_new_item_end))
            self.sample_end = f_new_item_end
            return True
        elif not a_truncate:
            f_new_start_seconds = \
                f_region_length_seconds - f_actual_sample_length
            f_beats_total = f_new_start_seconds / f_seconds_per_beat
            self.start_beat = f_beats_total
            return True
        else:
            return False

    def clone(self):
        return pydaw_audio_item.from_arr(str(self).strip("\n").split("|"))

    @staticmethod
    def from_str(f_str):
        return pydaw_audio_item.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_audio_item(*a_arr)
        return f_result


def envelope_to_automation(self, a_is_cc, a_tempo):
    " In the automation viewer clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    #  Smooth the array by sampling smaller and then larger
    f_arr = pydaw_util.np_resample(f_arr, int(f_length_beats * 4.0))
    f_arr = pydaw_util.np_resample(f_arr, f_point_count)
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        f_index = int(f_start / 4.0)
        f_start = f_start % 4.0
        if a_is_cc:
            f_val = pydaw_clip_value(f_point * 127.0, 0.0, 127.0)
            f_result.append((pydaw_cc(f_start, 0, f_val), f_index))
        else:
            f_val = pydaw_clip_value(f_point, 0.0, 1.0)
            f_result.append((pydaw_pitchbend(f_start, f_val), f_index))
    return f_result

def envelope_to_notes(self, a_tempo):
    " In the piano roll clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)  # 64th note resolution
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    f_arr = pydaw_util.np_resample(f_arr, f_point_count)
    f_current_note = None
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    f_thresh = pydaw_db_to_lin(-24.0)
    f_has_been_less = False

    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        if f_point > f_thresh:
            if not f_current_note:
                f_has_been_less = False
                f_current_note = [f_start, 0.25, f_point, f_point]
            else:
                if f_point > f_current_note[2]:
                    f_current_note[2] = f_point
                else:
                    f_has_been_less = True
                if f_point < f_current_note[3]:
                    f_current_note[3] = f_point
                if f_has_been_less and \
                f_point >= f_current_note[3] * 2.0:
                    f_current_note[1] = f_start - f_current_note[0]
                    f_result.append(f_current_note)
                    f_current_note = [f_start, 0.25, f_point, f_point]
        else:
            if f_current_note:
                f_current_note[1] = f_start - f_current_note[0]
                f_result.append(f_current_note)
                f_current_note = None
    f_result2 = []
    for f_pair in f_result:
        f_index = int(f_pair[0] / 4.0)
        f_start = f_pair[0] % 4.0
        f_vel = pydaw_clip_value((f_pair[2] * 70.0) + 40.0, 1.0, 127.0)
        f_result2.append(
            (str(pydaw_note(f_start, f_pair[1], 60, f_vel)), f_index))
    return f_result2


class DawNextMidiFile:
    """ Convert the MIDI file at a_file to a dict of channel#:pydaw_item
        @a_file:  The path to the MIDI file
        @a_project:  An instance of DawNextProject
    """
    def __init__(self, a_file, a_project):
        f_item_list = pydaw_util.load_midi_file(a_file)
        self.result_dict = {}

        for f_event in f_item_list:
            if f_event.length >= pydaw_min_note_length:
                f_velocity = f_event.ev.velocity
                f_beat = f_event.start_beat
                print("f_beat : {}".format(f_beat))
                f_pitch = f_event.ev.note
                f_length = f_event.length
                f_channel = f_event.ev.channel
                f_key = int(f_channel)
                if not f_key in self.result_dict:
                    f_uid = a_project.create_empty_item()
                    self.result_dict[f_key] = a_project.get_item_by_uid(f_uid)
                f_note = pydaw_note(f_beat, f_length, f_pitch, f_velocity)
                self.result_dict[f_key].add_note(f_note) #, a_check=False)
            else:
                print("Ignoring note event with <= zero length")
        for f_item in self.result_dict.values():
            a_project.save_item_by_uid(f_item.uid, f_item)
        self.channel_count = self.get_channel_count()

    def get_channel_count(self):
        return max(self.result_dict) if self.result_dict else 0



