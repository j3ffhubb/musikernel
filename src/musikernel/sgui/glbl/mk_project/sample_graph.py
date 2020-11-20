from sgui.lib import *
from sgui.lib.util import *
from sgui.mkqt import *
import numpy
import os


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
            f_vol = util.pydaw_db_to_lin(a_audio_item.vol)
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

