from .tracks import TrackSend
from mkpy.libpydaw import *
from mkpy.libpydaw.pydaw_util import *
from mkpy.mkqt import *


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


