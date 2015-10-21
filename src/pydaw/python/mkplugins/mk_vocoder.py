# -*- coding: utf-8 -*-
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

from libpydaw.pydaw_widgets import *
from libpydaw.translate import _

MK_VOCODER_WET = 0
MK_VOCODER_MODULATOR = 1
MK_VOCODER_CARRIER = 2

MK_VOCODER_PORT_MAP = {
    "Wet":MK_VOCODER_WET,
    "Modulator":MK_VOCODER_MODULATOR,
    "Carrier":MK_VOCODER_CARRIER,
}

MK_VOCODER_TEXT = _(
"""Route the carrier signal to the plugin's main input,
and route the modulator signal to the track's
sidechain input.""")


class mk_vocoder_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MK Vocoder"
        self.set_window_title(a_track_name)
        self.is_instrument = False
        #self.layout.setSizeConstraint(QLayout.SetFixedSize)
        f_knob_size = DEFAULT_KNOB_SIZE

        self.groupbox_gridlayout = QGridLayout()
        self.layout.addLayout(self.groupbox_gridlayout)

        self.wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), MK_VOCODER_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, 0, KC_TENTH, self.port_dict)
        self.wet_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.modulator_knob = pydaw_knob_control(
            f_knob_size, _("Modulator"), MK_VOCODER_MODULATOR,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, -500, KC_TENTH, self.port_dict)
        self.modulator_knob.add_to_grid_layout(self.groupbox_gridlayout, 9)

        self.carrier_knob = pydaw_knob_control(
            f_knob_size, _("Carrier"), MK_VOCODER_CARRIER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, -500, KC_TENTH, self.port_dict)
        self.carrier_knob.add_to_grid_layout(self.groupbox_gridlayout, 6)

        self.layout.addWidget(QLabel(MK_VOCODER_TEXT))
        self.scrollarea_widget.setFixedHeight(240)
        self.scrollarea_widget.setFixedWidth(360)
        self.open_plugin_file()
        self.set_midi_learn(MK_VOCODER_PORT_MAP)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MK Vocoder - {}".format(self.track_name))

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)

    def ui_message(self, a_name, a_value):
        pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


