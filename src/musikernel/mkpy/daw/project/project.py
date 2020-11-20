from . import _shared
from .atm_region import DawAtmRegion
from .audio_item import DawAudioItem
from .item import pydaw_item
from .seq_item import pydaw_sequencer_item
from .sequencer import pydaw_sequencer
from mkpy import glbl
from mkpy import plugins as _plugins
from mkpy.daw.osc import DawOsc
from mkpy.glbl.mk_project import *
from mkpy.lib import history
from mkpy.lib.util import *
from mkpy.lib.translate import _
from mkpy.log import LOG
from mkpy.mkqt import *
import os
import re


PIXMAP_BEAT_WIDTH = 48
PIXMAP_TILE_HEIGHT = 32

pydaw_folder_daw = os.path.join("projects", "daw")
pydaw_folder_items = os.path.join(pydaw_folder_daw, "items")
pydaw_folder_tracks = os.path.join(pydaw_folder_daw, "tracks")

FILE_SEQUENCER = os.path.join(pydaw_folder_daw, "sequencer.txt")
pydaw_file_regions_atm = os.path.join(pydaw_folder_daw, "automation.txt")
pydaw_file_routing_graph = os.path.join(pydaw_folder_daw, "routing.txt")
pydaw_file_midi_routing = os.path.join(
    pydaw_folder_daw,
    "midi_routing.txt",
)
pydaw_file_pyitems = os.path.join(pydaw_folder_daw, "items.txt")
pydaw_file_takes = os.path.join(pydaw_folder_daw, "takes.txt")
pydaw_file_pytracks = os.path.join(pydaw_folder_daw, "tracks.txt")
pydaw_file_pyinput = os.path.join(pydaw_folder_daw, "input.txt")
pydaw_file_notes = os.path.join(pydaw_folder_daw, "notes.txt")

class DawProject(glbl.AbstractProject):
    def __init__(self, a_with_audio):
        self.undo_context = 0
        self.TRACK_COUNT = _shared.TRACK_COUNT_ALL
        self.last_item_number = 1
        self.last_region_number = 1
        self.clear_history()
        self.painter_path_cache = {}
        self.pixmap_cache_unscaled = {}
        self.IPC = DawOsc(a_with_audio)
        self.suppress_updates = False

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        f_result = glbl.AbstractProject.save_file(
            self, a_folder, a_file, a_text, a_force_new)
        if f_result:
            f_existed, f_old = f_result
            f_history_file = history.history_file(
                a_folder, a_file, a_text, f_old, f_existed)
            self.history_files.append(f_history_file)
            if not util.IS_A_TTY:
                LOG.info(str(f_history_file))

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
            f_commit = history.history_commit(
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
            self.project_folder, pydaw_folder_daw)
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
            LOG.info("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

        if a_notify_osc:
            self.IPC.pydaw_open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            LOG.info(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

        self.save_file("", FILE_SEQUENCER, str(pydaw_sequencer()))
        self.create_file("", pydaw_file_pyitems, pydaw_terminating_char)
        f_tracks = pydaw_tracks()
        for i in range(_shared.TRACK_COUNT_ALL):
            f_tracks.add_track(i, pydaw_track(
                a_track_uid=i, a_track_pos=i,
                a_name="Master" if i == 0 else "track{}".format(i)))
            plugins = glbl.pydaw_track_plugins()
            for i2 in range(_plugins.TOTAL_PLUGINS_PER_TRACK):
                plugins.plugins.append(glbl.pydaw_track_plugin(i2, 0, -1))
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
        """ @a_midi_file:  An instance of DawMidiFile """
        f_sequencer = self.get_region()
        f_active_tracks = [
            x + a_track_offset
            for x in a_midi_file.result_dict
            if x + a_track_offset < _shared.TRACK_COUNT_ALL
        ]
        f_end_beat = max(x.get_length() for x in
            a_midi_file.result_dict.values())
        f_sequencer.clear_range(f_active_tracks, a_beat_offset, f_end_beat)
        for k,v in a_midi_file.result_dict.items():
            f_track = a_track_offset + int(k)
            if f_track >= _shared.TRACK_COUNT_ALL:
                break
            f_item_ref = pydaw_sequencer_item(
                f_track, a_beat_offset, v.get_length(), v.uid)
            f_sequencer.add_item_ref_by_uid(f_item_ref)
        self.save_region(f_sequencer)

    def get_atm_region(self):
        if os.path.isfile(self.automation_file):
            with open(self.automation_file) as f_file:
                return DawAtmRegion.from_str(f_file.read())
        else:
            return DawAtmRegion()

    def save_atm_region(self, a_region):
        self.save_file(pydaw_folder_daw, "automation.txt", str(a_region))
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
            a_item:  DawAudioItem
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
            return glbl.mk_project.AudioInputTracks.from_str(f_str)
        else:
            return glbl.mk_project.AudioInputTracks()

    def save_recorded_items(
            self, a_item_name, a_mrec_list, a_overdub,
            a_sr, a_start_beat, a_end_beat, a_audio_inputs,
            a_sample_count, a_file_name):
        LOG.info("\n".join(a_mrec_list))

        f_audio_files_dict = {}

        for f_i, f_ai in zip(range(len(a_audio_inputs)), a_audio_inputs):
            f_val = f_ai.get_value()
            if f_val.rec:
                f_path = os.path.join(
                    glbl.PROJECT.audio_tmp_folder, "{}.wav".format(f_i))
                if os.path.isfile(f_path):
                    f_file_name = "-".join(
                        str(x) for x in (a_file_name, f_i, f_ai.get_name()))
                    f_new_path = os.path.join(
                        glbl.PROJECT.audio_rec_folder, f_file_name)
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
                    f_uid = glbl.PROJECT.get_wav_uid_by_name(f_new_path)
                    sg = glbl.PROJECT.get_sample_graph_by_uid(f_uid)

                    f_audio_files_dict[f_i] = (
                        f_new_path, f_uid, sg.frame_count,
                        f_val.output, f_val.sidechain)
                else:
                    LOG.error("Error, path did not exist: {}".format(f_path))

        f_audio_frame = 0

        f_mrec_items = [x.split("|") for x in a_mrec_list]
        f_mrec_items.sort(key=lambda x: int(x[-1]))
        LOG.info("\n".join(str(x) for x in f_mrec_items))
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
                f_start = util.pydaw_clip_value(f_start, 0.0, f_end)
                f_end = util.pydaw_clip_value(f_end, f_start, 1000.0)
                f_audio_item = DawAudioItem(
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
                LOG.info("Using tick length for:")
                f_sample_count = f_tick - f_note.start_sample
                f_seconds = float(f_sample_count) / float(a_sr)
                f_note.set_length(f_seconds * f_beats_per_second)
            LOG.info(f_note_tracker[a_track_num].pop(f_note_num))

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
                LOG.info("Loop event")
                f_audio_frame += a_sample_count
                continue

            self.rec_item = self.rec_take[f_track]

            if f_type == "on":
                f_note_num, f_velocity, f_tick = (int(x) for x in f_event[3:])
                LOG.info("New note: {} {}".format(f_beat, f_note_num))
                f_note = pydaw_note(f_beat, 1.0, f_note_num, f_velocity)
                f_note.start_sample = f_tick
                if f_note_num in f_note_tracker[f_track]:
                    LOG.info("Terminating note early: {}".format(
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
                    LOG.error("Error:  note event not in note tracker")
            elif f_type == "cc":
                f_port, f_val, f_tick = f_event[3:]
                f_port = int(f_port)
                f_val = float(f_val)
                f_cc = pydaw_cc(f_beat, f_port, f_val)
                self.rec_item.add_cc(f_cc)
            elif f_type == "pb":
                f_val = float(f_event[3]) / 8192.0
                f_val = util.pydaw_clip_value(f_val, -1.0, 1.0)
                f_pb = pydaw_pitchbend(f_beat, f_val)
                self.rec_item.add_pb(f_pb)
            else:
                LOG.error("Invalid mrec event type {}".format(f_type))

        for f_uid, f_item in f_items_to_save.items():
            f_item.fix_overlaps()
            self.save_item_by_uid(f_uid, f_item, a_new_item=True)

        self.save_region(f_sequencer)
        self.commit("Record")

    def reorder_tracks(self, a_dict):
        glbl.IPC.pause_engine()
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
        glbl.IPC.resume_engine()
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

    def get_item_path(
        self,
        a_uid,
        a_px_per_beat,
        a_height,
        a_tempo,
    ):
        a_uid = int(a_uid)
        f_key = (a_px_per_beat, a_height, round(a_tempo, 1))
        if (
            a_uid in self.painter_path_cache
            and
            f_key in self.painter_path_cache[a_uid]
        ):
            return self.painter_path_cache[a_uid][f_key]
        else:
            if a_uid not in self.pixmap_cache_unscaled:
                f_item_obj = self.get_item_by_uid(a_uid)
                f_path = f_item_obj.painter_path(
                    PIXMAP_BEAT_WIDTH,
                    PIXMAP_TILE_HEIGHT,
                    a_tempo,
                )
                self.pixmap_cache_unscaled[a_uid] = f_path
            if a_uid not in self.painter_path_cache:
                self.painter_path_cache[a_uid] = {}
            f_x, f_y = util.scale_sizes(
                PIXMAP_BEAT_WIDTH,
                PIXMAP_TILE_HEIGHT,
                a_px_per_beat,
                a_height,
            )
            f_transform = QTransform()
            f_transform.scale(f_x, f_y)
            self.painter_path_cache[a_uid][f_key] = (
                self.pixmap_cache_unscaled[a_uid],
                f_transform,
                f_x,
                f_y,
            )
            return self.painter_path_cache[a_uid][f_key]

    def save_item_by_uid(self, a_uid, a_item, a_new_item=False):
        a_uid = int(a_uid)
        if a_uid in self.painter_path_cache:
            self.painter_path_cache.pop(a_uid)
        if a_uid in self.pixmap_cache_unscaled:
            self.pixmap_cache_unscaled.pop(a_uid)
        if not self.suppress_updates:
            self.save_file(
                pydaw_folder_items,
                str(a_uid),
                str(a_item),
                a_new_item,
            )
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
            @a_track: glbl.pydaw_track_plugins
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

