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


MK_COMP_THRESHOLD = 0
MK_COMP_RATIO = 1
MK_COMP_KNEE = 2
MK_COMP_ATTACK = 3
MK_COMP_RELEASE = 4
MK_COMP_GAIN = 5
MK_COMP_MODE = 6
MK_COMP_RMS_TIME = 7
MK_COMP_UI_MSG_ENABLED = 8


MK_COMP_PORT_MAP = {}


class mk_comp_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, *args, **kwargs):
        pydaw_abstract_plugin_ui.__init__(self, *args, **kwargs)
        self._plugin_name = "MK Compressor"
        self.is_instrument = False

        self.preset_manager = None
        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        self.delay_hlayout = QHBoxLayout()
        self.layout.addLayout(self.delay_hlayout)

        f_knob_size = DEFAULT_KNOB_SIZE

        self.groupbox_gridlayout = QGridLayout()
        self.delay_hlayout.addLayout(self.groupbox_gridlayout)

        self.thresh_knob = pydaw_knob_control(
            f_knob_size, _("Thresh"), MK_COMP_THRESHOLD,
            self.plugin_rel_callback, self.plugin_val_callback,
            -360, -60, -240, KC_TENTH, self.port_dict, self.preset_manager)
        self.thresh_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.ratio_knob = pydaw_knob_control(
            f_knob_size, _("Ratio"), MK_COMP_RATIO,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 100, 20, KC_TENTH, self.port_dict, self.preset_manager)
        self.ratio_knob.add_to_grid_layout(self.groupbox_gridlayout, 7)

        self.knee_knob = pydaw_knob_control(
            f_knob_size, _("Knee"), MK_COMP_KNEE,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 120, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.knee_knob.add_to_grid_layout(self.groupbox_gridlayout, 15)

        self.attack_knob = pydaw_knob_control(
            f_knob_size, _("Attack"), MK_COMP_ATTACK,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 500, 50, KC_MILLISECOND, self.port_dict, self.preset_manager)
        self.attack_knob.add_to_grid_layout(self.groupbox_gridlayout, 21)

        self.release_knob = pydaw_knob_control(
            f_knob_size, _("Release"), MK_COMP_RELEASE,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 500, 100, KC_MILLISECOND, self.port_dict, self.preset_manager)
        self.release_knob.add_to_grid_layout(self.groupbox_gridlayout, 22)

        self.gain_knob = pydaw_knob_control(
            f_knob_size, _("Gain"), MK_COMP_GAIN,
            self.plugin_rel_callback, self.plugin_val_callback,
            -360, 360, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.gain_knob.add_to_grid_layout(self.groupbox_gridlayout, 30)

        self.mono_combobox = pydaw_combobox_control(
            90, _("Mode"), MK_COMP_MODE,
            self.plugin_rel_callback, self.plugin_val_callback,
            [_("Peak"), _("RMS")], self.port_dict, 0, self.preset_manager)
        self.mono_combobox.add_to_grid_layout(self.groupbox_gridlayout, 36)

        self.rms_time_knob = pydaw_knob_control(
            f_knob_size, _("RMS Time"), MK_COMP_RMS_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 5, 2, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.rms_time_knob.add_to_grid_layout(self.groupbox_gridlayout, 37)

        self.peak_meter = peak_meter(16, False)
        self.delay_hlayout.addWidget(self.peak_meter.widget)

        self.ui_msg_enabled = pydaw_null_control(
            MK_COMP_UI_MSG_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(MK_COMP_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close(self):
        self.enable_ui_msg(False)
        pydaw_abstract_plugin_ui.widget_close(self)

    def widget_show(self):
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            print("Enabling UI messages")
            self.plugin_val_callback(
                MK_COMP_UI_MSG_ENABLED, 1.0)
        else:
            print("Disabling UI messages")
            self.plugin_val_callback(
                MK_COMP_UI_MSG_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            self.peak_meter.set_value([a_value] * 2)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)

