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


SCC_THRESHOLD = 0
SCC_RATIO = 1
SCC_ATTACK = 2
SCC_RELEASE = 3
SCC_WET = 4
SCC_UI_MSG_ENABLED = 5


SCC_PORT_MAP = {
    "Wet": SCC_WET
}


class scc_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, *args, **kwargs):
        pydaw_abstract_plugin_ui.__init__(self, *args, **kwargs)
        self._plugin_name = "Sidechain Comp."
        self.is_instrument = False

        self.preset_manager = None
        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        self.delay_hlayout = QHBoxLayout()
        self.layout.addLayout(self.delay_hlayout)

        f_knob_size = DEFAULT_KNOB_SIZE

        self.widget.setObjectName("plugin_groupbox")
        self.reverb_groupbox_gridlayout = QGridLayout()
        self.delay_hlayout.addLayout(self.reverb_groupbox_gridlayout)

        self.thresh_knob = pydaw_knob_control(
            f_knob_size, _("Thresh"), SCC_THRESHOLD,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, -6, -24, KC_INTEGER, self.port_dict, self.preset_manager)
        self.thresh_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 3)

        self.ratio_knob = pydaw_knob_control(
            f_knob_size, _("Ratio"), SCC_RATIO,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 100, 20, KC_TENTH, self.port_dict, self.preset_manager)
        self.ratio_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 7)

        self.attack_knob = pydaw_knob_control(
            f_knob_size, _("Attack"), SCC_ATTACK,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 100, 20, KC_INTEGER, self.port_dict, self.preset_manager)
        self.attack_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 15)

        self.release_knob = pydaw_knob_control(
            f_knob_size, _("Release"), SCC_RELEASE,
            self.plugin_rel_callback, self.plugin_val_callback,
            30, 300, 50, KC_INTEGER, self.port_dict, self.preset_manager)
        self.release_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 18)

        self.wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), SCC_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_INTEGER, self.port_dict, self.preset_manager)
        self.wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 21)

        self.peak_meter = peak_meter(16, False)
        self.delay_hlayout.addWidget(self.peak_meter.widget)

        self.ui_msg_enabled = pydaw_null_control(
            SCC_UI_MSG_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(SCC_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close(self):
        self.enable_ui_msg(False)
        pydaw_abstract_plugin_ui.widget_close(self)

    def widget_show(self):
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            print("Enabling UI messages")
            self.plugin_val_callback(SCC_UI_MSG_ENABLED, 1.0)
        else:
            print("Disabling UI messages")
            self.plugin_val_callback(SCC_UI_MSG_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            self.peak_meter.set_value([a_value] * 2)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)


