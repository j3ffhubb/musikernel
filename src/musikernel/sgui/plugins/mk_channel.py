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

from sgui.widgets import *
from sgui.lib.translate import _

MKCHNL_VOL_SLIDER = 0
MKCHNL_GAIN = 1
MKCHNL_PAN = 2
MKCHNL_LAW = 3

MKCHNL_PORT_MAP = {
    "Volume": MKCHNL_VOL_SLIDER,
    "Pan": MKCHNL_PAN,
}

class mkchnl_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, *args, **kwargs):
        pydaw_abstract_plugin_ui.__init__(self, *args, **kwargs)
        self._plugin_name = "MKCHNL"
        self.is_instrument = False
        f_knob_size = 42
        self.gain_gridlayout = QGridLayout()
        if self.is_mixer:
            self.layout.addLayout(self.gain_gridlayout)
        else:
            self.hlayout = QHBoxLayout()
            self.layout.addLayout(self.hlayout)
            self.hlayout.addLayout(self.gain_gridlayout)
        self.gain_knob = pydaw_knob_control(
            f_knob_size, _("Gain"), MKCHNL_GAIN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -2400, 2400, 0, KC_DECIMAL, self.port_dict, None)
        self.gain_knob.add_to_grid_layout(self.gain_gridlayout, 0)
        self.gain_knob.value_label.setMinimumWidth(55)

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
            QtCore.Qt.Vertical if self.is_mixer else QtCore.Qt.Horizontal,
            "Vol", MKCHNL_VOL_SLIDER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -5000, 0, 0, KC_DECIMAL, self.port_dict)
        if self.is_mixer:
            self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)
            self.volume_slider.control.setSizePolicy(
                QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            self.volume_slider_layout = QGridLayout()
            self.volume_slider_layout.setSizeConstraint(QLayout.SetMaximumSize)
            self.hlayout.addLayout(self.volume_slider_layout, 1)
            self.volume_slider.add_to_grid_layout(
                self.volume_slider_layout, 0, a_alignment=None)
        self.volume_slider.value_label.setMinimumWidth(180)
        self.open_plugin_file()
        self.set_midi_learn(MKCHNL_PORT_MAP)

    def plugin_rel_callback(self, a_val1=None, a_val2=None):
        self.save_plugin_file()
