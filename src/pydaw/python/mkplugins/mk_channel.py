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

MKCHNL_VOL_SLIDER = 0
MKCHNL_GAIN = 1
MKCHNL_PAN = 2
MKCHNL_LAW = 3

MKCHNL_PORT_MAP = {
    "Volume": MKCHNL_VOL_SLIDER,
    "Pan": MKCHNL_PAN,
}

class mkchnl_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MKCHNL"
        self.is_instrument = False
        #self.layout.setSizeConstraint(QLayout.SetFixedSize)
        f_knob_size = 32
        self.gain_gridlayout = QGridLayout()
        self.layout.addLayout(self.gain_gridlayout)
        self.gain_knob = pydaw_knob_control(
            f_knob_size, _("Gain"), MKCHNL_GAIN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -2400, 2400, 0, KC_DECIMAL, self.port_dict, None)
        self.gain_knob.add_to_grid_layout(self.gain_gridlayout, 0)

        self.pan_knob = pydaw_knob_control(
            f_knob_size, _("Pan"), MKCHNL_PAN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, None)
        self.pan_knob.add_to_grid_layout(self.gain_gridlayout, 1)
        self.pan_law_knob = pydaw_knob_control(
            f_knob_size, _("Law"), MKCHNL_LAW,
            self.plugin_rel_callback, self.plugin_val_callback,
            -600, 0, -300, KC_DECIMAL, self.port_dict, None)
        self.pan_law_knob.add_to_grid_layout(self.gain_gridlayout, 2)

        self.volume_gridlayout = QGridLayout()
        self.layout.addLayout(self.volume_gridlayout)
        self.volume_slider = pydaw_slider_control(
            QtCore.Qt.Vertical, "Vol", MKCHNL_VOL_SLIDER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -5000, 0, 0, KC_DECIMAL, self.port_dict)
        self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
        self.volume_slider.control.setMinimumHeight(240)
        self.volume_slider.control.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.widget.setFixedWidth(130)
        self.volume_slider.value_label.setMinimumWidth(91)
        self.widget.setWidgetResizable(True)
        self.open_plugin_file()
        self.set_midi_learn(MKCHNL_PORT_MAP)

    def plugin_rel_callback(self, a_val1=None, a_val2=None):
        self.save_plugin_file()
