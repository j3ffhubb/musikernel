from . import _shared
from .region_marker import pydaw_loop_marker
from .seq_item import pydaw_sequencer_item
from .tempo_marker import pydaw_tempo_marker
from mkpy.libmk.mk_project import *
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *


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
        for f_i in range(_shared.TRACK_COUNT_ALL):
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
        for f_i in range(_shared.TRACK_COUNT_ALL):
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
                            _shared.pydaw_sequencer_marker(
                                *f_item_arr[2:]
                            )
                        )
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


