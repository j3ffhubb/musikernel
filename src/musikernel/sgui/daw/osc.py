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

from sgui.lib.util import (
    bool_to_int,
    get_wait_file_path,
    wait_for_finished_file,
)

from sgui import glbl


class DawOsc(glbl.AbstractIPC):
    def __init__(self, a_with_audio=False,
             a_configure_path="/musikernel/daw"):
        glbl.AbstractIPC.__init__(self, a_with_audio, a_configure_path)

    def save_song(self):
        self.send_configure("ss", "")

    def open_song(self, a_project_folder, a_first_open=True):
        self.send_configure(
            "os",  "|".join(str(x) for x in
            (bool_to_int(a_first_open), a_project_folder)))

    def save_item(self, a_uid):
        self.send_configure("si", str(a_uid))

    def save_region(self):
        self.send_configure("sr", "")

    def en_playback(self, a_mode, a_beat="0"):
        self.send_configure(
            "enp", "|".join(str(x) for x in (a_mode, a_beat)))

    def set_loop_mode(self, a_mode):
        self.send_configure("loop", str(a_mode))

    def set_solo(self, a_track_num, a_bool):
        self.send_configure(
            "solo", "|".join(str(x) for x in
            (a_track_num, bool_to_int(a_bool))))

    def set_mute(self, a_track_num, a_bool):
        self.send_configure(
            "mute", "|".join(str(x) for x in
            (a_track_num, bool_to_int(a_bool))))

    def set_plugin(
    self, a_track_num, a_index, a_plugin_index, a_uid, a_on):
        self.send_configure(
            "pi", "|".join(str(x) for x in
            (a_track_num, a_index, a_plugin_index,
             a_uid, bool_to_int(a_on))))

    def update_track_send(self):
        self.send_configure("ts", "")

    def save_tracks(self):
        self.send_configure("st", "")

    def save_atm_region(self):
        self.send_configure("sa", "")

    def offline_render(self, a_start_beat, a_end_beat, a_file_name):
        self.send_configure(
            "or", "|".join(str(x) for x in
            (a_start_beat, a_end_beat, a_file_name)))

    def we_export(self, a_file_name):
        self.send_configure("wex", "{}".format(a_file_name))

    def set_overdub_mode(self, a_is_on):
        """ a_is_on should be a bool """
        self.send_configure("od", bool_to_int(a_is_on))

    def panic(self):
        self.send_configure("panic", "")

    def audio_per_item_fx(
            self, a_item_uid, a_audio_item_index, a_port_num, a_val):
        self.send_configure(
            "paif", "|".join(str(x) for x in
             (a_item_uid, a_audio_item_index, a_port_num, a_val)))

    def glue_audio(
            self, a_file_name, a_region_index, a_start_bar_index,
            a_end_bar_index, a_item_indexes):
        f_index_arr = [str(x) for x in a_item_indexes]
        self.send_configure("ga", "|".join(str(x) for x in
           (a_file_name, a_region_index, a_start_bar_index, a_end_bar_index,
           "|".join(f_index_arr))))
        if self.with_osc:
            f_wait_file = get_wait_file_path(a_file_name)
            wait_for_finished_file(f_wait_file)

    def midi_device(self, a_is_on, a_device_num, a_track_num):
        self.send_configure(
            "md", "|".join(str(x) for x in
            (bool_to_int(a_is_on), a_device_num, a_track_num)))

    def set_pos(self, a_beat):
        self.send_configure("pos", str(a_beat))

    def save_audio_inputs(self):
        self.send_configure("ai", "")
